#!/bin/bash
# setup.sh - chuẩn bị môi trường cho Streamlit Cloud

# Đặt JAVA_HOME cho openjdk-17
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "JAVA_HOME set to $JAVA_HOME"
java -version
javac -version
