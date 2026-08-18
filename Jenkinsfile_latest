pipeline {

    agent {
        kubernetes {

            yaml '''
apiVersion: v1
kind: Pod

spec:

  hostNetwork: true
  dnsPolicy: Default

  containers:

    # ==========================================
    # KANIKO
    # Build and push Docker image
    # ==========================================

    - name: kaniko
      image: gcr.io/kaniko-project/executor:v1.23.2-debug

      command:
        - /busybox/cat

      tty: true

      resources:
        requests:
          memory: "512Mi"
          cpu: "250m"

        limits:
          memory: "4Gi"
          cpu: "2"

      volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker


    # ==========================================
    # GIT
    # Update GitOps repository
    # ==========================================

    - name: git
      image: alpine/git:latest

      command:
        - /bin/sh

      tty: true

      resources:
        requests:
          memory: "64Mi"
          cpu: "50m"

        limits:
          memory: "256Mi"
          cpu: "500m"


    # ==========================================
    # SLACK WEBHOOK
    # No Jenkins Slack plugin required
    # ==========================================

    - name: slack
      image: curlimages/curl:latest

      command:
        - /bin/sh
        - -c
        - cat

      tty: true

      resources:
        requests:
          memory: "32Mi"
          cpu: "25m"

        limits:
          memory: "128Mi"
          cpu: "200m"


  volumes:

    - name: docker-config
      emptyDir: {}

'''

            defaultContainer 'kaniko'
        }
    }


    // ==========================================
    // GLOBAL ENVIRONMENT VARIABLES
    // ==========================================

    environment {

        DOCKER_IMAGE =
            'muskanpatel71198/postgres-rag-ollama'

        GITOPS_REPO =
            'https://github.com/muskan7860/postgres-rag-ollama-gitops.git'

        IMAGE_TAG =
            "${BUILD_NUMBER}"
    }


    stages {


        // ==================================================
        // STAGE 1
        // BUILD + PUSH DOCKER IMAGE
        // ==================================================

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
                            echo "DOCKER HUB AUTHENTICATION"
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

                            echo "Build Number: $BUILD_NUMBER"

                            echo "Image:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"


                            /kaniko/executor \
                              --context="$WORKSPACE" \
                              --dockerfile="$WORKSPACE/Dockerfile" \
                              --destination="docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER" \
                              --destination="docker.io/$DOCKER_USERNAME/postgres-rag-ollama:latest" \
                              --cache=true \
                              --cache-ttl=24h


                            echo "=========================================="
                            echo "DOCKER IMAGE PUSHED SUCCESSFULLY"
                            echo "=========================================="

                            echo "Versioned Image:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"

                            echo ""

                            echo "Latest Image:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:latest"
                        '''
                    }
                }
            }
        }


        // ==================================================
        // STAGE 2
        // UPDATE GITOPS REPOSITORY
        // ==================================================

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
                            echo "CURRENT KUBERNETES IMAGE"
                            echo "=========================================="

                            grep "image:" app-deployment.yaml || true


                            echo "=========================================="
                            echo "UPDATING IMAGE TAG"
                            echo "=========================================="

                            sed -i \
                              "s|image:.*postgres-rag-ollama:.*|image: docker.io/muskanpatel71198/postgres-rag-ollama:$BUILD_NUMBER|g" \
                              app-deployment.yaml


                            echo "=========================================="
                            echo "UPDATED KUBERNETES IMAGE"
                            echo "=========================================="

                            grep "image:" app-deployment.yaml


                            echo "=========================================="
                            echo "CONFIGURING GIT"
                            echo "=========================================="

                            git config user.name "Jenkins CI"

                            git config user.email "jenkins@localhost"


                            echo "=========================================="
                            echo "GIT STATUS"
                            echo "=========================================="

                            git status


                            echo "=========================================="
                            echo "COMMITTING GITOPS CHANGE"
                            echo "=========================================="

                            git add app-deployment.yaml


                            git commit \
                              -m "Update postgres-rag-ollama image to build $BUILD_NUMBER" \
                              || echo "No changes to commit"


                            echo "=========================================="
                            echo "PUSHING GITOPS CHANGE"
                            echo "=========================================="

                            git push origin main


                            echo "=========================================="
                            echo "GITOPS UPDATE SUCCESSFUL"
                            echo "=========================================="

                            echo "Argo CD will detect this Git change"
                            echo "and automatically synchronize Kubernetes."
                        '''
                    }
                }
            }
        }
    }


    // ==================================================
    // POST ACTIONS
    // ==================================================

    post {


        // ==================================================
        // SUCCESS
        // ==================================================

        success {

            echo '''
==========================================
CI/CD PIPELINE SUCCESS
==========================================

Docker image built successfully.

Docker image pushed successfully.

GitOps repository updated successfully.

Argo CD will automatically detect
the GitOps change and synchronize
the Kubernetes application.

==========================================
'''


            script {

                try {

                    echo "Sending SUCCESS notification to Slack via webhook..."


                    container('slack') {

                        withCredentials([

                            string(
                                credentialsId: 'postgres-rag-ollama-slack',
                                variable: 'SLACK_WEBHOOK'
                            )

                        ]) {

                            sh '''
                                set +x

                                PAYLOAD=$(cat <<EOF
{
  "text": "✅ *CI/CD PIPELINE SUCCESS*\\n\\n*Application:* postgres-rag-ollama\\n*Jenkins Build:* #${BUILD_NUMBER}\\n*Status:* SUCCESS\\n*Docker Image:* docker.io/muskanpatel71198/postgres-rag-ollama:${BUILD_NUMBER}\\n*Docker Hub:* Image built and pushed successfully.\\n*GitOps:* app-deployment.yaml updated successfully.\\n*Argo CD:* Automatic synchronization will deploy the new image.\\n*Build URL:* ${BUILD_URL}"
}
EOF
)

                                curl \
                                  --fail \
                                  --silent \
                                  --show-error \
                                  -X POST \
                                  -H 'Content-Type: application/json' \
                                  --data "$PAYLOAD" \
                                  "$SLACK_WEBHOOK"
                            '''
                        }
                    }


                    echo "Slack SUCCESS notification sent."

                }

                catch (Exception e) {

                    echo "=========================================="

                    echo "WARNING: Slack notification failed."

                    echo "CI/CD deployment itself was successful."

                    echo "Slack failure will NOT mark the pipeline failed."

                    echo "=========================================="

                    echo "Slack error: ${e.getMessage()}"
                }
            }
        }


        // ==================================================
        // FAILURE
        // ==================================================

        failure {

            echo '''
==========================================
CI/CD PIPELINE FAILED
==========================================

Check Jenkins console output.

==========================================
'''


            script {

                try {

                    echo "Sending FAILURE notification to Slack via webhook..."


                    container('slack') {

                        withCredentials([

                            string(
                                credentialsId: 'postgres-rag-ollama-slack',
                                variable: 'SLACK_WEBHOOK'
                            )

                        ]) {

                            sh '''
                                set +x

                                PAYLOAD=$(cat <<EOF
{
  "text": "❌ *CI/CD PIPELINE FAILED*\\n\\n*Application:* postgres-rag-ollama\\n*Jenkins Build:* #${BUILD_NUMBER}\\n*Status:* FAILED\\n*Action:* Please check Jenkins console logs.\\n*Build URL:* ${BUILD_URL}"
}
EOF
)

                                curl \
                                  --fail \
                                  --silent \
                                  --show-error \
                                  -X POST \
                                  -H 'Content-Type: application/json' \
                                  --data "$PAYLOAD" \
                                  "$SLACK_WEBHOOK"
                            '''
                        }
                    }


                    echo "Slack FAILURE notification sent."

                }

                catch (Exception e) {

                    echo "=========================================="

                    echo "WARNING: Slack failure notification could not be sent."

                    echo "Slack notification failure will not hide the original pipeline failure."

                    echo "=========================================="

                    echo "Slack error: ${e.getMessage()}"
                }
            }
        }


        // ==================================================
        // ALWAYS
        // ==================================================

        always {

            echo '''
==========================================
PIPELINE EXECUTION FINISHED
==========================================
'''
        }
    }
}
