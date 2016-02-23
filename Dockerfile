FROM python:latest

# Install nginx
ENV NGINX_VERSION 1.9.11-1~jessie
RUN apt-key adv --keyserver hkp://pgp.mit.edu:80 --recv-keys 573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62 \
	&& echo "deb http://nginx.org/packages/mainline/debian/ jessie nginx" >> /etc/apt/sources.list \
	&& apt-get update \
	&& apt-get install -y ca-certificates nginx=${NGINX_VERSION} gettext-base \
	&& rm -rf /var/lib/apt/lists/*

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

# Add deploy+flask files
ADD flask/ /data_server
ADD deploy/supervisor.conf /etc/supervisor.conf

# Nginx daemon off
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Install dependencies of the server
RUN pip install git+git://github.com/Supervisor/supervisor.git@f99d017de2e921c8e6e12b64525ca306ce18bfa9
RUN pip install gunicorn
RUN pip install -r /data_server/requirements.txt

# Nginx conf
ADD deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD supervisord -c /etc/supervisor.conf -n
