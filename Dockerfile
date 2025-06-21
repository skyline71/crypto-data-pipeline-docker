FROM debian:stretch-slim

RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian-security stretch/updates main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y wget openjdk-8-jdk

# Устанавливаем Hadoop 2.7.7
RUN wget https://archive.apache.org/dist/hadoop/common/hadoop-2.7.7/hadoop-2.7.7.tar.gz && \
    tar -xzf hadoop-2.7.7.tar.gz -C /usr/local && \
    mv /usr/local/hadoop-2.7.7 /usr/local/hadoop && \
    rm hadoop-2.7.7.tar.gz

RUN wget http://archive.apache.org/dist/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz && \
    tar -xzf sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -C /opt && \
    mv /opt/sqoop-1.4.7.bin__hadoop-2.6.0 /opt/sqoop && \
    rm sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz

RUN wget https://dev.mysql.com/get/Downloads/Connector-J/mysql-connector-java-8.0.30.tar.gz && \
    tar -xzf mysql-connector-java-8.0.30.tar.gz && \
    cp mysql-connector-java-8.0.30/mysql-connector-java-8.0.30.jar /opt/sqoop/lib/ && \
    rm -rf mysql-connector-java-8.0.30*

RUN wget https://repo1.maven.org/maven2/org/apache/avro/avro/1.8.2/avro-1.8.2.jar && \
    cp avro-1.8.2.jar /opt/sqoop/lib/ && \
    rm avro-1.8.2.jar

RUN wget https://repo1.maven.org/maven2/org/apache/avro/avro-mapred/1.8.2/avro-mapred-1.8.2-hadoop2.jar && \
    cp avro-mapred-1.8.2-hadoop2.jar /opt/sqoop/lib/ && \
    rm avro-mapred-1.8.2-hadoop2.jar

RUN wget https://repo1.maven.org/maven2/commons-lang/commons-lang/2.6/commons-lang-2.6.jar && \
    cp commons-lang-2.6.jar /opt/sqoop/lib/ && \
    rm commons-lang-2.6.jar

RUN apt-get install -y mysql-client

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV HADOOP_HOME=/usr/local/hadoop
ENV HADOOP_COMMON_HOME=/usr/local/hadoop
ENV HADOOP_MAPRED_HOME=/usr/local/hadoop
ENV SQOOP_HOME=/opt/sqoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$SQOOP_HOME/bin

CMD ["bash"]
