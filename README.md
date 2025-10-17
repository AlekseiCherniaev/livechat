# Livechat

# mongo key

mkdir -p docker/mongo
openssl rand -base64 756 > docker/mongo/keyfile.pem
chmod 400 docker/mongo/keyfile.pem
sudo chown 999:999 docker/mongo/keyfile.pem