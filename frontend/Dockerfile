FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/public/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
