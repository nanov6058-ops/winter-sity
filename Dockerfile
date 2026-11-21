FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget unzip ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN wget -q https://github.com \
    && unzip Godot_v4.7.2-stable_linux.x86_64.zip \
    && mv Godot_v4.7.2-stable_linux.x86_64 server \
    && rm Godot_v4.7.2-stable_linux.x86_64.zip \
    && chmod +x server
COPY WinterTown.pck .
EXPOSE 8080
CMD ["./server", "--headless", "--main-pack", "WinterTown.pck", "--server"]
