pipeline {

    agent any

    environment {
        DOCKER_IMAGE = 'muskanpatel71198/postgres-rag-ollama'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out application source code...'
                checkout scm
            }
        }

        stage('Python Tests') {
            steps {
                echo 'Running Python tests...'

                sh '''
                    python3 -m venv .ci-venv
                    . .ci-venv/bin/activate

                    python -m pip install --upgrade pip
                    pip install -r requirements.txt

                    python -m pytest -v
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image ${DOCKER_IMAGE}:${IMAGE_TAG}"

                sh '''
                    docker build \
                        -t ${DOCKER_IMAGE}:${IMAGE_TAG} \
                        -t ${DOCKER_IMAGE}:latest \
                        .
                '''
            }
        }

        stage('Docker Push') {
            steps {
                echo 'Pushing Docker image to Docker Hub...'

                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login \
                            -u "$DOCKER_USERNAME" \
                            --password-stdin

                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        docker push ${DOCKER_IMAGE}:latest

                        docker logout
                    '''
                }
            }
        }
    }

    post {

        success {
            echo "CI pipeline completed successfully."

            slackSend(
                channel: '#jenkins',
                color: 'good',
                message: """
SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}

Application: postgres-rag-ollama
Status: SUCCESS
Docker Image: ${env.DOCKER_IMAGE}:${env.IMAGE_TAG}

Build URL:
${env.BUILD_URL}
"""
            )
        }

        failure {
            echo "CI pipeline failed."

            slackSend(
                channel: '#jenkins',
                color: 'danger',
                message: """
FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}

Application: postgres-rag-ollama
Status: FAILED

Build URL:
${env.BUILD_URL}
"""
            )
        }

        always {
            echo "Pipeline finished."
        }
    }
}