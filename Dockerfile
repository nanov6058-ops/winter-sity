FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget unzip ca-certificates socat && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV GH_HOST=https://github.com
ENV GH_REPO=godotengine/godot-builds/releases/download
ENV GODOT_VER=4.7.2-stable
ENV GODOT_ZIP=Godot_v4.7.2-stable_linux.x86_64.zip

RUN wget -q -O godot.zip "${GH_HOST}/${GH_REPO}/${GODOT_VER}/${GODOT_ZIP}" \
    && unzip godot.zip \
    && mv Godot_v4.7.2-stable_linux.x86_64 server \
    && rm godot.zip \
    && chmod +x server

COPY WinterTown.pck .
EXPOSE 8080 8000 3000 80

CMD ["sh", "-c", "socat TCP-LISTEN:8000,fork TCP:127.0.0.1:8080 & socat TCP-LISTEN:3000,fork TCP:127.0.0.1:8080 & socat TCP-LISTEN:80,fork TCP:127.0.0.1:8080 & ./server --headless --main-pack WinterTown.pck --server"]
