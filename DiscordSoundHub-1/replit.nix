{pkgs}: {
  deps = [
    pkgs.libopus
    pkgs.ffmpeg
    pkgs.pkg-config
    pkgs.libffi
    pkgs.libsodium
    pkgs.ffmpeg-full
    pkgs.postgresql
    pkgs.openssl
  ];
}
