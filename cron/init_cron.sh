pkg install cronie termux-services
# Reload Termux and session
sv-enable crond
crontab job