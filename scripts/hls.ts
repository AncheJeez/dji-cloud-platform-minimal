const video = document.getElementById('video') as HTMLVideoElement | null;
const streamUrl = '/public/stream.m3u8'; // cambia si tu .m3u8 tiene otra ruta

if (!video) {
  console.error('Video element not found');
} else if (Hls.isSupported()) {
  const hls = new Hls();
  hls.loadSource(streamUrl);
  hls.attachMedia(video);
} else if (video.canPlayType('application/vnd.apple.mpegurl')) {
  video.src = streamUrl; // Safari
} else {
  console.error('HLS not supported in this browser.');
}