pipeline {

    agent any

    environment {

        // Docker image
        DOCKER_IMAGE = 'muskanpatel71198/postgres-rag-ollama'

        // Jenkins automatically provides BUILD_NUMBER
        IMAGE_TAG = "${BUILD_NUMBER}"

        // GitOps repository
        GITOPS_REPO = 'https://github.com/muskan7860/postgres-rag-ollama-gitops.git'
        GITOPS_BRANCH = 'main'

        // GitHub username
        GITHUB_USERNAME = 'muskan7860'
    }

    stages {

        // =========================================================
        // 1. CHECKOUT APPLICATION CODE
        // =========================================================

        stage('Checkout') {

            steps {

                echo '========================================='
                echo 'Checking out application source code'
                echo '========================================='

                checkout scm
            }
        }


        // =========================================================
        // 2. PYTHON TESTS
        // =========================================================

        stage('Python Tests') {

            steps {

                echo '========================================='
                echo 'Running Python tests'
                echo '========================================='

                sh '''
                    set -e

                    python3 -m venv .ci-venv

                    . .ci-venv/bin/activate

                    python -m pip install --upgrade pip

                    pip install -r requirements.txt

                    python -m pytest -v
                '''
            }
        }


        // =========================================================
        // 3. DOCKER BUILD
        // =========================================================

        stage('Docker Build') {

            steps {

                echo '========================================='
                echo "Building Docker image"
                echo "Image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                echo '========================================='

                sh '''
                    set -e

                    docker build \
                        -t ${DOCKER_IMAGE}:${IMAGE_TAG} \
                        -t ${DOCKER_IMAGE}:latest \
                        .
                '''
            }
        }


        // =========================================================
        // 4. DOCKER PUSH
        // =========================================================

        stage('Docker Push') {

            steps {

                echo '========================================='
                echo 'Pushing Docker image to Docker Hub'
                echo '========================================='

                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        set -e

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


        // =========================================================
        // 5. UPDATE GITOPS REPOSITORY
        // =========================================================

        stage('Update GitOps') {

            steps {

                echo '========================================='
                echo 'Updating GitOps repository'
                echo "New image tag: ${IMAGE_TAG}"
                echo '========================================='

                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-creds',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_TOKEN'
                    )
                ]) {

                    sh '''
                        set -e

                        rm -rf gitops

                        git clone \
                            -b ${GITOPS_BRANCH} \
                            https://${GIT_USERNAME}:${GIT_TOKEN}@github.com/muskan7860/postgres-rag-ollama-gitops.git \
                            gitops

                        cd gitops

                        echo "Before update:"
                        grep "image:" app-deployment.yaml || true

                        echo "Updating Docker image tag..."

                        sed -i \
                            "s#image: ${DOCKER_IMAGE}:.*#image: ${DOCKER_IMAGE}:${IMAGE_TAG}#" \
                            app-deployment.yaml

                        echo "After update:"
                        grep "image:" app-deployment.yaml

                        git config user.name "Jenkins CI"

                        git config user.email "jenkins@localhost"

                        git add app-deployment.yaml

                        git diff --cached

                        git commit \
                            -m "Update postgres-rag-ollama image to ${IMAGE_TAG}"

                        git push origin ${GITOPS_BRANCH}
                    '''
                }
            }
        }
    }


    // =============================================================
    // POST ACTIONS
    // =============================================================

    post {

        // =========================================================
        // SUCCESS
        // =========================================================

        success {

            echo '========================================='
            echo 'CI/CD PIPELINE SUCCESS'
            echo '========================================='

            withCredentials([
                string(
                    credentialsId: 'postgres-rag-ollama-slack',
                    variable: 'SLACK_WEBHOOK'
                )
            ]) {

                sh '''
                    curl -X POST \
                        -H "Content-Type: application/json" \
                        --data "{
                            \\"text\\": \\"SUCCESS: postgres-rag-ollama #${BUILD_NUMBER}\\\\n\\\\nDocker Image: ${DOCKER_IMAGE}:${IMAGE_TAG}\\\\n\\\\nDocker image pushed successfully.\\\\nGitOps repository updated successfully.\\\\nArgo CD will detect the Git change and synchronize the application.\\\\n\\\\nBuild URL: ${BUILD_URL}\\"
                        }" \
                        "$SLACK_WEBHOOK"
                '''
            }
        }


        // =========================================================
        // FAILURE
        // =========================================================

        failure {

            echo '========================================='
            echo 'CI/CD PIPELINE FAILED'
            echo '========================================='

            withCredentials([
                string(
                    credentialsId: 'postgres-rag-ollama-slack',
                    variable: 'SLACK_WEBHOOK'
                )
            ]) {

                sh '''
                    curl -X POST \
                        -H "Content-Type: application/json" \
                        --data "{
                            \\"text\\": \\"FAILED: postgres-rag-ollama #${BUILD_NUMBER}\\\\n\\\\nThe Jenkins pipeline failed.\\\\n\\\\nBuild URL: ${BUILD_URL}\\"
                        }" \
                        "$SLACK_WEBHOOK"
                '''
            }
        }


        // =========================================================
        // ALWAYS
        // =========================================================

        always {

            echo '========================================='
            echo 'Pipeline execution finished'
            echo '========================================='
        }
    }
}
