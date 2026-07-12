// ==========================================================================
// Jenkinsfile — DevOps Health Dashboard CI/CD Pipeline
// Stages: Checkout -> Install -> Unit Tests -> Build Image -> Push -> Deploy
//         -> Health Check -> Cleanup
//
// Required Jenkins credentials (configure in Jenkins Credentials Manager):
//   dockerhub-credentials  (Username with password) — DockerHub login
//   deploy-ssh-key         (SSH Username with private key) — optional, for
//                          remote deploys via SSH
// ==========================================================================

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        IMAGE_NAME       = "yourdockerhubuser/devops-health-dashboard"
        IMAGE_TAG        = "${env.BUILD_NUMBER}"
        DOCKERHUB_CREDS  = credentials('dockerhub-credentials')
        CONTAINER_NAME   = "devops-health-dashboard"
        APP_PORT         = "5000"
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
                echo "Creating virtual environment and installing dependencies..."
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo "Running pytest suite..."
                sh '''
                    . .venv/bin/activate
                    pytest --junitxml=reports/junit.xml
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
                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "Pushing image to DockerHub..."
                sh '''
                    echo "$DOCKERHUB_CREDS_PSW" | docker login -u "$DOCKERHUB_CREDS_USR" --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    docker logout
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying container..."
                sh '''
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p ${APP_PORT}:5000 \
                        -v /var/run/docker.sock:/var/run/docker.sock:ro \
                        -e FLASK_ENV=production \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo "Waiting for application to become healthy..."
                sh '''
                    for i in $(seq 1 10); do
                        if curl -sf http://localhost:${APP_PORT}/health; then
                            echo "Application is healthy."
                            exit 0
                        fi
                        echo "Not ready yet, retrying in 3s..."
                        sleep 3
                    done
                    echo "Health check failed after retries."
                    exit 1
                '''
            }
        }

        stage('Cleanup') {
            steps {
                echo "Cleaning up dangling images and build cache..."
                sh '''
                    docker image prune -f
                    rm -rf .venv
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully — build #${env.BUILD_NUMBER}"
        }
        failure {
            echo "❌ Pipeline failed — check the stage logs above."
        }
        always {
            cleanWs()
        }
    }
}
