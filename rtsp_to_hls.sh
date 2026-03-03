ffmpeg -i "rtsp://USUARIO:PASS@IP:PUERTO/ruta" \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -c:a aac -ar 44100 -b:a 128k \
  -f hls -hls_time 2 -hls_list_size 6 -hls_flags delete_segments \
  ./public/stream.m3u8