#!/bin/bash
# setup.sh - chuẩn bị môi trường cho Streamlit Cloud

sudo apt-get update -y
sudo apt-get install -y openjdk-17-jdk

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "JAVA_HOME=$JAVA_HOME"
java -version
javac -version
which java
which javac
