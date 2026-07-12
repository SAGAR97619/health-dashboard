pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
        DOCKERHUB_USER = 'sagarsaini9761'
        IMAGE_NAME = "${DOCKERHUB_USER}/health-dashboard"
        IMAGE_TAG = "${BUILD_NUMBER}"

        CONTAINER_NAME = "health-dashboard"
        APP_PORT = "5000"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate

                    mkdir -p reports
                    pytest --junitxml=reports/junit.xml || true
                '''
            }

            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker Image..."

                sh '''
                    docker build \
                    -t ${IMAGE_NAME}:${IMAGE_TAG} \
                    -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Login to Docker Hub') {
            steps {
                sh '''
                    echo "$DOCKERHUB_CREDENTIALS_PSW" | docker login \
                    -u "$DOCKERHUB_CREDENTIALS_USR" \
                    --password-stdin
                '''
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                sh '''
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Deploy Container') {
            steps {
                sh '''
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true

                    docker pull ${IMAGE_NAME}:latest

                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p ${APP_PORT}:5000 \
                        -v /var/run/docker.sock:/var/run/docker.sock:ro \
                        -e FLASK_ENV=production \
                        ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 10

                    curl -f http://localhost:${APP_PORT}/health
                '''
            }
        }

        stage('Cleanup') {
            steps {
                sh '''
                    docker image prune -f
                    docker logout
                    rm -rf .venv
                '''
            }
        }
    }

    post {

        success {
            echo "==========================================="
            echo "Build Successful"
            echo "Docker Image Pushed Successfully"
            echo "Application Deployed Successfully"
            echo "==========================================="
        }

        failure {
            echo "==========================================="
            echo "Pipeline Failed"
            echo "Check Jenkins Console Output"
            echo "==========================================="
        }

        always {
            cleanWs()
        }
    }
}
