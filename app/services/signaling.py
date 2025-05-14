from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import Dict
from app.dependencies.redis_manager import redis_client
import time

router = APIRouter(prefix="/signaling")

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# WebSocket 연결된 사용자 목록
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    logging.info(f"✅ {user_id} 이/가 웹소켓에 연결됨")

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if not message_type:
                logging.warning("🚨 잘못된 요청: 'type'이 누락됨")
                continue

            response_data = {"type": message_type}

            # 통화 요청 (Incoming Call)
            if message_type == "incoming_call":
                receiver_id = data.get("receiver_id")
                if not receiver_id:
                    logging.error("🚨 잘못된 요청: 'receiver_id'가 누락됨")
                    continue

                response_data.update({"caller_id": user_id})

                if receiver_id in active_connections:
                    await active_connections[receiver_id].send_json(response_data)
                    logging.info(
                        f"📞 [incoming_call] {user_id} -> {receiver_id} 통화 요청 전송 성공"
                    )
                else:
                    logging.warning(
                        f"⚠️ [incoming_call] 수신자가 연결되지 않음: {receiver_id}"
                    )

            # 통화 거절 (Call Reject)
            elif message_type == "call_reject":
                caller_id = data.get("caller_id")
                if caller_id in active_connections:
                    await active_connections[caller_id].send_json(response_data)
                    logging.info(f"🚫 [call_reject] {caller_id} 통화 거절 성공")
                else:
                    logging.warning(
                        f"⚠️ [call_reject] 발신자가 연결되지 않음: {caller_id}"
                    )

            # 통화 수락 (Call Answer) → Redis에서 call_id 가져옴
            elif message_type == "call_answer":
                caller_id = data.get("caller_id")
                receiver_id = user_id  # 이 메시지는 수신자가 보내는 거니까!

                # Redis에서 call_id 가져오기
                call_id = redis_client.get(f"accept:{caller_id}:{receiver_id}")
                if not call_id:
                    logging.warning(
                        f"🚨 [call_answer] call_id 없음! caller_id={caller_id}, receiver_id={receiver_id}"
                    )
                    continue

                response_data.update({"caller_id": caller_id, "call_id": call_id})

                if caller_id in active_connections:
                    await active_connections[caller_id].send_json(response_data)
                    logging.info(
                        f"✅ [call_answer] {caller_id} 통화 수락 성공 (call_id: {call_id})"
                    )
                else:
                    logging.warning(
                        f"⚠️ [call_answer] 발신자가 연결되지 않음: {caller_id}"
                    )

            # 통화 종료 (Call End)
            elif message_type == "call_end":

                call_id = data.get("call_id")
                caller_id = data.get("caller_id")
                receiver_id = data.get("receiver_id")

                # 종료 요청을 누가 보냈는지 확인
                if user_id == caller_id:
                    target_id = receiver_id

                elif user_id == receiver_id:
                    target_id = caller_id

                else:
                    logging.warning(f"🚨 [call_end] 비정상 요청: user_id={user_id}")
                    continue

                response_data.update(
                    {
                        "type": "call_end",
                        "call_id": call_id,
                        "from": user_id,  # 누가 끊었는지 알려주기
                    }
                )

                if target_id in active_connections:
                    await active_connections[target_id].send_json(response_data)
                    logging.info(
                        f"🔚 [call_end] {user_id}가 통화 종료함, 상대 {target_id}에게 알림 성공"
                    )
                else:
                    logging.warning(
                        f"⚠️ [call_end] 종료 통지하려 했지만 상대방 연결 없음: {target_id}"
                    )

            # Offer 전송 (WebRTC Offer) → Redis에서 call_id 가져옴
            elif message_type == "offer":
                caller_id = data.get("caller_id")
                receiver_id = data.get("receiver_id")

                # Redis에서 call_id 가져오기
                call_id = redis_client.get(f"accept:{caller_id}:{receiver_id}")

                if not call_id:
                    logging.warning(
                        f"🚨 [offer] call_id가 없음! caller_id={caller_id}, receiver_id={receiver_id}"
                    )
                    continue

                sdp = data.get("sdp")
                media_constraints = data.get("media_constraints", {})

                response_data.update(
                    {
                        "call_id": call_id,
                        "sdp": sdp,
                        "media_constraints": media_constraints,
                    }
                )

                if receiver_id in active_connections:
                    await active_connections[receiver_id].send_json(response_data)
                    logging.info(f"📡 [offer] {call_id} Offer 전송 성공")

                redis_client.setex(f"offer:{call_id}", 3600, "active")

            # Answer 전송 (WebRTC Answer) → Redis에서 call_id 가져옴
            elif message_type == "answer":
                caller_id = data.get("caller_id")
                receiver_id = data.get("receiver_id")

                # Redis에서 call_id 가져오기
                call_id = redis_client.get(f"accept:{caller_id}:{receiver_id}")

                if not call_id:
                    logging.warning(
                        f"🚨 [answer] call_id가 없음! caller_id={caller_id}, receiver_id={receiver_id}"
                    )
                    continue

                if not redis_client.exists(f"offer:{call_id}"):
                    logging.warning(f"🚨 [answer] Offer가 실행되지 않음: {call_id}")
                    continue

                sdp = data.get("sdp")

                response_data.update(
                    {"caller_id": caller_id, "call_id": call_id, "sdp": sdp}
                )

                if caller_id in active_connections:
                    await active_connections[caller_id].send_json(response_data)
                    logging.info(f"✅ [answer] {call_id} Answer 전송 성공")

                redis_client.setex(f"answer:{call_id}", 3600, "active")

            # ICE Candidate 전송 (WebRTC ICE Candidate) → Redis에서 call_id 가져옴
            elif message_type == "ice_candidate":
                caller_id = data.get("caller_id")
                receiver_id = data.get("receiver_id")

                # Redis에서 call_id 가져오기
                call_id = redis_client.get(f"accept:{caller_id}:{receiver_id}")

                if not call_id:
                    logging.warning(
                        f"🚨 [ice_candidate] call_id가 없음! caller_id={caller_id}, receiver_id={receiver_id}"
                    )
                    continue

                if not redis_client.exists(f"answer:{call_id}"):
                    logging.warning(
                        f"🚨 [ice_candidate] Answer가 실행되지 않음: {call_id}"
                    )
                    continue

                candidate = data.get("candidate")

                response_data.update(
                    {
                        "call_id": call_id,
                        "candidate": candidate,
                    }
                )

                if receiver_id in active_connections:
                    await active_connections[receiver_id].send_json(response_data)
                    logging.info(f"❄️ [ice_candidate] {call_id} ICE Candidate 전송 성공")

                redis_client.setex(f"ice_candidate:{call_id}", 3600, "active")

    except WebSocketDisconnect:
        logging.info(f"❌ {user_id} 연결 종료")
        del active_connections[user_id]
    except Exception as e:
        logging.error(f"🚨 WebSocket 오류: {e}")
    finally:
        if user_id in active_connections:
            del active_connections[user_id]
