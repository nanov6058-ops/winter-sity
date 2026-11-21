FROM ubuntu:22.04
WORKDIR /app
COPY WinterTown.x86_64 .
COPY WinterTown.pck .
RUN chmod +x WinterTown.x86_64
EXPOSE 8080
CMD ["./WinterTown.x86_64", "--headless", "--server"]
