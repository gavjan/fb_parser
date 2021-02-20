cd .. # [Project Directory]

git pull

if python3 run.py >.log_file 2>.err_file ; then
  mkdir -p ".log/$(date +%d-%m-%Y)"
  cp .log_file ".log/$(date +%d-%m-%Y)/$(date +%H-%M).log"
else
  mkdir -p ".err/$(date +%d-%m-%Y)"
  cat .err_file >> .log_file
  cp .log_file .err_file
  cp .err_file ".err/$(date +%d-%m-%Y)/$(date +%H-%M).err"
  cp .log_file ".log/$(date +%d-%m-%Y)/$(date +%H-%M).log"


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



