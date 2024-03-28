import argparse
import asyncio
import json
import logging
import os
import platform
import ssl
import uuid
import time
import av
from fractions import Fraction
from picamera2 import Picamera2

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender

ROOT = os.path.dirname(__file__)

relay = None
webcam = None
cam = Picamera2()
cam.configure(cam.create_video_configuration())
cam.start()
pcs = {}

class PiCameraTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()

    async def recv(self):
        img = cam.capture_array()

        pts = time.time() * 1000000
        new_frame = av.VideoFrame.from_ndarray(img, format='rgba')
        new_frame.pts = int(pts)
        new_frame.time_base = Fraction(1,1000000)
        return new_frame

async def webrtc(request):
    params = await request.json()
    if params["type"] == "request":
        pc = RTCPeerConnection()
        pc_id = "PeerConnection(%s)" % uuid.uuid4()
        pcs[pc_id] = pc

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                # pcs.discard(pc) @TODO

        cam = PiCameraTrack()
        pc.addTrack(cam)
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        while True:
            if pc.iceGatheringState == "complete":
                break

        @pc.on("signalingstatechange")
        async def on_signalingstatechange():
            print("Signaling state is %s" % pc.signalingState)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "id": pc_id, "iceServers": []}
            ),
        )
    elif params["type"] == "answer":
        pc = pcs[params["id"]]

        if not pc:
            return web.Response(
                content_type="application
        await pc.setRemoteDescription(RTCSessionDescription(sdp=params["sdp"], type=params["type"]))

        return web.Response(
            content_type="application/json",
            text=json.dumps(
               {}
            ),
        )

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs.values()]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RatRig V-Core VAOC (WebRTC camera-streamer)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_post("/webrtc", webrtc)
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)
