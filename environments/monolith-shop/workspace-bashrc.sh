# Цветное приглашение командной строки
export PS1='\[\e[0;32m\]student@prod-polygon\[\e[0m\]:\[\e[0;34m\]\w\[\e[0m\]\$ '

# Алиасы
alias ll='ls -la --color=auto'
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias docker='sudo docker'

# Автодополнение
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# Приветствие при подключении
echo ""
echo "  ██████╗ ██████╗  ██████╗ ██████╗ "
echo "  ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗"
echo "  ██████╔╝██████╔╝██║   ██║██║  ██║"
echo "  ██╔═══╝ ██╔══██╗██║   ██║██║  ██║"
echo "  ██║     ██║  ██║╚██████╔╝██████╔╝"
echo "  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ "
echo ""
echo "  прод/полигон — учебная среда"
echo "  Используйте docker ps, docker logs и другие команды"
echo ""