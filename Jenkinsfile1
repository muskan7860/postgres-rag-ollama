pipeline {

    agent {
        kubernetes {

            yaml '''
apiVersion: v1
kind: Pod

spec:

  containers:

    # ==========================================
    # Python container
    # Used for application tests
    # ==========================================

    - name: python
      image: python:3.12-slim
      command:
        - /bin/sh
      tty: true


    # ==========================================
    # Kaniko container
    # Used to build and push Docker image
    # ==========================================

    - name: kaniko
      image: gcr.io/kaniko-project/executor:v1.23.2-debug
      command:
        - /busybox/cat
      tty: true

      volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker


    # ==========================================
    # Git container
    # Used to update GitOps repository
    # ==========================================

    - name: git
      image: alpine/git:latest
      command:
        - /bin/sh
      tty: true


  volumes:

    - name: docker-config
      emptyDir: {}

'''
            defaultContainer 'python'
        }
    }


    environment {

        DOCKER_IMAGE = 'muskanpatel71198/postgres-rag-ollama'

        IMAGE_TAG = "${BUILD_NUMBER}"

        GITOPS_REPO =
            'https://github.com/muskan7860/postgres-rag-ollama-gitops.git'

    }


    stages {


        // ============================================================
        // STAGE 1
        // CHECKOUT APPLICATION
        // ============================================================

        stage('Checkout') {

            steps {

                echo '''
==========================================
CHECKOUT APPLICATION SOURCE CODE
==========================================
'''

                checkout scm
            }
        }


        // ============================================================
        // STAGE 2
        // PYTHON TESTS
        // ============================================================

        stage('Python Tests') {

            steps {

                container('python') {

                    echo '''
==========================================
RUNNING PYTHON TESTS
==========================================
'''

                    sh '''
                        set -e

                        python --version
                        pip --version

                        python -m pip install --upgrade pip

                        pip install -r requirements.txt

                        python -m pytest -v
                    '''
                }
            }
        }


        // ============================================================
        // STAGE 3
        // BUILD + PUSH DOCKER IMAGE USING KANIKO
        // ============================================================

        stage('Docker Build & Push') {

            steps {

                container('kaniko') {

                    withCredentials([

                        usernamePassword(

                            credentialsId: 'dockerhub-creds',

                            usernameVariable: 'DOCKER_USERNAME',

                            passwordVariable: 'DOCKER_PASSWORD'
                        )

                    ]) {

                        sh '''

                            set -e

                            echo "=========================================="
                            echo "CREATING DOCKER HUB AUTHENTICATION"
                            echo "=========================================="

                            mkdir -p /kaniko/.docker


                            AUTH=$(printf "%s:%s" \
                              "$DOCKER_USERNAME" \
                              "$DOCKER_PASSWORD" \
                              | base64 \
                              | tr -d '\\n')


                            cat > /kaniko/.docker/config.json <<EOF
{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "$AUTH"
    }
  }
}
EOF


                            echo "=========================================="
                            echo "BUILDING DOCKER IMAGE"
                            echo "=========================================="


                            /kaniko/executor \
                              --context="$WORKSPACE" \
                              --dockerfile="$WORKSPACE/Dockerfile" \
                              --destination="docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"


                            echo "=========================================="
                            echo "DOCKER IMAGE PUSHED"
                            echo "=========================================="

                            echo "Image:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"

                        '''
                    }
                }
            }
        }


        // ============================================================
        // STAGE 4
        // UPDATE GITOPS REPOSITORY
        // ============================================================

        stage('Update GitOps') {

            steps {

                container('git') {

                    withCredentials([

                        usernamePassword(

                            credentialsId: 'github-creds',

                            usernameVariable: 'GIT_USERNAME',

                            passwordVariable: 'GIT_TOKEN'
                        )

                    ]) {

                        sh '''

                            set -e


                            echo "=========================================="
                            echo "CLONING GITOPS REPOSITORY"
                            echo "=========================================="


                            rm -rf postgres-rag-ollama-gitops


                            git clone \
                              https://$GIT_USERNAME:$GIT_TOKEN@github.com/muskan7860/postgres-rag-ollama-gitops.git \
                              postgres-rag-ollama-gitops


                            cd postgres-rag-ollama-gitops


                            echo "=========================================="
                            echo "CURRENT IMAGE"
                            echo "=========================================="


                            grep "image:" app-deployment.yaml || true


                            echo "=========================================="
                            echo "UPDATING IMAGE TAG"
                            echo "=========================================="


                            sed -i \
                              "s|image: muskanpatel71198/postgres-rag-ollama:.*|image: muskanpatel71198/postgres-rag-ollama:$BUILD_NUMBER|g" \
                              app-deployment.yaml


                            echo "=========================================="
                            echo "UPDATED IMAGE"
                            echo "=========================================="


                            grep "image:" app-deployment.yaml


                            echo "=========================================="
                            echo "GIT STATUS"
                            echo "=========================================="


                            git status


                            git config user.name "Jenkins CI"

                            git config user.email "jenkins@localhost"


                            git add app-deployment.yaml


                            git commit \
                              -m "Update postgres-rag-ollama image to build $BUILD_NUMBER" \
                              || echo "No changes to commit"


                            git push origin main


                            echo "=========================================="
                            echo "GITOPS REPOSITORY UPDATED"
                            echo "=========================================="

                        '''
                    }
                }
            }
        }
    }


    // ================================================================
    // POST ACTIONS
    // ================================================================

    post {


        success {

            echo '''
==========================================
CI/CD PIPELINE SUCCESS
==========================================

Application tests passed.

Docker image built and pushed.

GitOps manifest updated.

Argo CD will detect the Git change
and synchronize Kubernetes.

==========================================
'''


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
                        \\"text\\": \\"SUCCESS: postgres-rag-ollama #${BUILD_NUMBER}\\\\n\\\\nDocker image: ${DOCKER_IMAGE}:${BUILD_NUMBER}\\\\n\\\\nGitOps repository updated successfully.\\\\n\\\\nArgo CD will synchronize the application.\\\\n\\\\nBuild URL: ${BUILD_URL}\\"
                      }" \
                      "$SLACK_WEBHOOK"

                '''
            }
        }


        failure {

            echo '''
==========================================
CI/CD PIPELINE FAILED
==========================================

Check Jenkins console output.

==========================================
'''


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


        always {

            echo '''
==========================================
PIPELINE EXECUTION FINISHED
==========================================
'''
        }
    }
}
