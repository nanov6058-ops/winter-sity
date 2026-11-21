FROM ubuntu:22.04
RUN apt-get update && apt-get install -y wget unzip ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN wget -q -O godot.zip https://github.com \
    && unzip godot.zip \
    && mv Godot_v4.7.2-stable_linux.x86_64 server \
    && rm godot.zip \
    && chmod +x server
COPY WinterTown.pck .
EXPOSE 8080
CMD ["./server", "--headless", "--main-pack", "WinterTown.pck", "--server"]
