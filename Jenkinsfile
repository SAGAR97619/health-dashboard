// ==========================================================================
// Jenkinsfile — DevOps Health Dashboard CI/CD Pipeline (GitHub Container Registry + EC2)
// Stages: Checkout -> Install -> Unit Tests -> Build Image -> Push (GHCR)
//         -> Deploy (on EC2, same host) -> Health Check -> Cleanup
//
// Required Jenkins credentials (Manage Jenkins -> Credentials):
//   ghcr-credentials   (Username with password)
//     Username = your GitHub username
//     Password = GitHub Personal Access Token with write:packages scope
// ==========================================================================

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {
        REGISTRY         = "ghcr.io"
        GITHUB_USER      = "SAGAR97619"        // <-- change this
        IMAGE_NAME       = "${REGISTRY}/${GITHUB_USER}/devops-health-dashboard"
        IMAGE_TAG        = "${env.BUILD_NUMBER}"
        GHCR_CREDS       = credentials('ghcr-credentials')
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
                echo "Building ${IMAGE_NAME}:${IMAGE_TAG}..."
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Push to GHCR') {
            steps {
                echo "Pushing image to GitHub Container Registry..."
                sh '''
                    echo "$GHCR_CREDS_PSW" | docker login ${REGISTRY} -u "$GHCR_CREDS_USR" --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    docker logout ${REGISTRY}
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying container on this host (EC2)..."
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
                sh '''
                    docker image prune -f
                    rm -rf .venv
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully — build #${env.BUILD_NUMBER}"
        }
        failure {
            echo "Pipeline failed — check the stage logs above."
        }
        always {
            cleanWs()
        }
    }
}
