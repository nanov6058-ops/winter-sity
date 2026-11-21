FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget unzip ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV GH_HOST=https://github.com
ENV GH_REPO=godotengine/godot-builds/releases/download
ENV GODOT_VER=4.6-stable
ENV GODOT_ZIP=Godot_v4.6-stable_linux.x86_64.zip

RUN wget -q -O godot.zip "${GH_HOST}/${GH_REPO}/${GODOT_VER}/${GODOT_ZIP}" \
    && unzip godot.zip \
    && mv Godot_v4.6-stable_linux.x86_64 server \
    && rm godot.zip \
    && chmod +x server

COPY WinterTown.pck .
EXPOSE 8080
CMD ["./server", "--headless", "--main-pack", "WinterTown.pck", "--server"]
