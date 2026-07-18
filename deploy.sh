#!/bin/bash

# Short Stay EC2 部署脚本
# 在EC2实例上运行此脚本进行自动部署

set -e  # 遇到错误立即退出

echo "========================================="
echo "Short Stay 部署脚本"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/var/www/short_stay"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${GREEN}Step 1: 更新系统软件包${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}Step 2: 安装必要软件${NC}"
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib git

echo -e "${GREEN}Step 3: 创建项目目录${NC}"
sudo mkdir -p /var/www
sudo chown -R $USER:$USER /var/www

echo -e "${GREEN}Step 4: 配置PostgreSQL${NC}"
echo -e "${YELLOW}请手动配置PostgreSQL数据库：${NC}"
echo "sudo -u postgres psql"
echo "CREATE DATABASE short_stay;"
echo "CREATE USER short_stay_user WITH PASSWORD 'your_password';"
echo "GRANT ALL PRIVILEGES ON DATABASE short_stay TO short_stay_user;"
echo "\q"
read -p "按Enter继续..."

echo -e "${GREEN}Step 5: 创建Python虚拟环境${NC}"
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}Step 6: 安装Python依赖${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Step 7: 配置Django${NC}"
echo -e "${YELLOW}请编辑 short_stay/production_settings.py${NC}"
echo "设置: SECRET_KEY, ALLOWED_HOSTS, 数据库密码"
read -p "配置完成后按Enter继续..."

echo -e "${GREEN}Step 8: 数据库迁移${NC}"
python manage.py migrate

echo -e "${GREEN}Step 9: 创建超级用户${NC}"
python manage.py createsuperuser

echo -e "${GREEN}Step 10: 收集静态文件${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}Step 11: 创建日志目录${NC}"
mkdir -p logs
chmod 755 logs

echo -e "${GREEN}Step 12: 配置Gunicorn服务${NC}"
sudo cp gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

echo -e "${GREEN}Step 13: 配置Nginx${NC}"
sudo cp nginx.conf /etc/nginx/sites-available/short_stay
sudo ln -sf /etc/nginx/sites-available/short_stay /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo -e "${GREEN}Step 14: 配置防火墙${NC}"
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo "========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "========================================="
echo "访问: http://$(curl -s ifconfig.me)"
echo ""
echo "有用的命令:"
echo "sudo systemctl restart gunicorn  # 重启Gunicorn"
echo "sudo systemctl restart nginx     # 重启Nginx"
echo "sudo journalctl -u gunicorn -f   # 查看Gunicorn日志"
