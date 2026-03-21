FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    nano \
    htop \
    net-tools \
    iputils-ping \
    dnsutils \
    netcat-openbsd \
    procps \
    lsof \
    jq \
    git \
    tree \
    less \
    bash-completion \
    ca-certificates \
    gnupg \
    sudo \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
       | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo \
       "deb [arch=$(dpkg --print-architecture) \
       signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/ubuntu \
       $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
       | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаём пользователя и добавляем в группу docker
RUN useradd -m -s /bin/bash student \
    && echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && groupadd -f docker \
    && usermod -aG docker student

COPY workspace-bashrc.sh /home/student/.bashrc
RUN chown student:student /home/student/.bashrc

USER student
WORKDIR /home/student

CMD ["/bin/bash", "-c", "while true; do sleep 1; done"]