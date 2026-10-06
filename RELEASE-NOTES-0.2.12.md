# PSA CarPlay 0.2.12-dev — draft hardware candidate

Continues 0.2.11; modes are USB, existing system hotspot, existing LAN. The app never creates or stops hotspots/P2P. System hotspot information is read live; unknown values require explicitly confirmed manual supplementation. Hotspot and LAN settings are separate. WAN availability is not a connection condition.

Bluetooth preparation runs alongside TCP/Bonjour setup; iAP2/MFi handoff remains gated by actual publication. IPv4 experiment retains dual-stack local sockets and allows one same-interface IPv6 alternative handoff after 12 seconds without repeating authentication or extending the original deadline. Bonjour control probes alternate routes serially rather than consuming all retries on one failed family; probing requires completed MFi.

Terminal events from the active AirPlay session are delivered before media/Bonjour cleanup. The UI detaches the old picture and requests the PSA home activity immediately; background cleanup retains the existing start-blocking gate. Bluetooth termination after handoff does not imply CarPlay loss. Full TEARDOWN and TCP EOF/error are terminal evidence; an unrelated auxiliary session cannot trigger this UI transition. Android 9 silent-peer keepalive latency still needs investigation and hardware validation.

No formal release, main merge, private keys, credentials, or real-device performance claims. Video decoding, rotation, audio routing, MFi implementation and USB transports are unchanged. Runtime lifecycle notifications and wireless endpoint fallback are explicitly reviewed exceptions to the protected protocol-file check.
