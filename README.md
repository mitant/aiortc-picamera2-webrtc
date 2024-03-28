# aiortc-picamera2-webrtc
webrtc implementation that mimics camera-streamer webrtc negotiation. useful for raspberry pi 5 &amp; ratrig vcore IDEX vaoc integration

# Intro
This small webserver leverages picamera2 and aiortc to present a webrtc endpoint that mimics the camera-streamer style webrtc negotiation.
It was created to simplify Raspberry Pi 5 klipper/mainsail picam integration as the loss of hardware encoding on the Pi 5 has led to compatibility
 problems with some camera-related libraries.

You don't need to use crowsnest with this.
You will need to update nginx configuration and add this as a background service.

# Notes
This is currently experimental and does not include instructions.  Instructions will be written up later.
