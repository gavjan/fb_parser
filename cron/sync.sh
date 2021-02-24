cd /data/data/com.termux/files/home/fb_parser # [Project Directory]

git pull

if curl https://students.mimuw.edu.pl/\~gc401929/.topsale/signal | grep FLUSH_DB; then
  rm .json/db.json;
  ssh mim "rm -f ~/public_html/.topsale/signal"
fi

if python3 run.py >.log_file 2>.err_file ; then
  mkdir -p ".log/$(date +%d-%m-%Y)"

  if [ -s .log_file ]; then
    ssh mim "mkdir -p ~/public_html/.topsale/log/$(date +%d-%m-%Y)"
    cp .log_file ".log/$(date +%d-%m-%Y)/$(date +%H-%M).log"
    scp .log_file mim:~/public_html/.topsale/log/"$(date +%d-%m-%Y)/$(date +%H-%M).log"
  fi
  scp output/db.xml mim:~/public_html/.topsale


else
  mkdir -p ".err/$(date +%d-%m-%Y)"
  cat .err_file >> .log_file
  cp .log_file .err_file

  ssh mim "mkdir -p ~/public_html/.topsale/err/$(date +%d-%m-%Y)"
  cp.err_file ".err/$(date +%d-%m-%Y)/$(date +%H-%M).err"
  scp.err_file mim:~/public_html/.topsale/err/"$(date +%d-%m-%Y)/$(date +%H-%M).err"

  sed -i "s/\"/'/g" .err_file
  curl "https://api.postmarkapp.com/email" \
  -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Postmark-Server-Token: $(cat cron/token.txt)" \
  -d "{
  \"From\": \"$(cat cron/mail)\",
  \"To\": \"$(cat cron/mail)\",
  \"Subject\": \"[Topsale] Sync Error\",
  \"TextBody\": \"$(cat .err_file)\",
  \"MessageStream\": \"outbound\"
}"
fi



