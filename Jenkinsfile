pipeline {

    // ==========================================================
    // KUBERNETES JENKINS AGENT
    // ==========================================================

    agent {
        kubernetes {

            yaml '''
apiVersion: v1
kind: Pod

spec:

  hostNetwork: true
  dnsPolicy: Default

  containers:


    # ==========================================================
    # KANIKO
    # Build and push application image
    # ==========================================================

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
          memory: "3Gi"
          cpu: "2"

      volumeMounts:

        - name: docker-config
          mountPath: /kaniko/.docker


    # ==========================================================
    # GIT
    #
    # Used for:
    # - GitOps repository
    # - Slack webhook via curl
    # ==========================================================

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


  volumes:

    - name: docker-config
      emptyDir: {}

'''

            defaultContainer 'kaniko'
        }
    }


    // ==========================================================
    // ENVIRONMENT
    // ==========================================================

    environment {

        DOCKER_IMAGE =
            'muskanpatel71198/postgres-rag-ollama'

        GITOPS_REPO =
            'https://github.com/muskan7860/postgres-rag-ollama-gitops.git'

        IMAGE_TAG =
            "${BUILD_NUMBER}"
    }


    // ==========================================================
    // PIPELINE
    // ==========================================================

    stages {


        // ======================================================
        // STAGE 1
        // DOCKER BUILD + PUSH
        // ======================================================

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

                            echo "Build Number : $BUILD_NUMBER"

                            echo "Image        : docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"


                            /kaniko/executor \
                                --context="$WORKSPACE" \
                                --dockerfile="$WORKSPACE/Dockerfile" \
                                --destination="docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER" \
                                --destination="docker.io/$DOCKER_USERNAME/postgres-rag-ollama:latest" \
                                --snapshot-mode=redo \
                                --cache=false


                            echo "=========================================="
                            echo "DOCKER IMAGE PUSHED SUCCESSFULLY"
                            echo "=========================================="

                            echo "Version:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:$BUILD_NUMBER"

                            echo ""

                            echo "Latest:"
                            echo "docker.io/$DOCKER_USERNAME/postgres-rag-ollama:latest"
                        '''
                    }
                }
            }
        }


        // ======================================================
        // STAGE 2
        // UPDATE GITOPS
        // ======================================================

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
                            echo "CURRENT APPLICATION IMAGES"
                            echo "=========================================="

                            grep "postgres-rag-ollama:" \
                                app-deployment.yaml \
                                || true


                            echo "=========================================="
                            echo "UPDATING IMAGE TAG"
                            echo "=========================================="

                            sed -i \
                                "s|image:.*postgres-rag-ollama:.*|image: docker.io/muskanpatel71198/postgres-rag-ollama:$BUILD_NUMBER|g" \
                                app-deployment.yaml


                            echo "=========================================="
                            echo "UPDATED APPLICATION IMAGES"
                            echo "=========================================="

                            grep "postgres-rag-ollama:" \
                                app-deployment.yaml


                            git config \
                                user.name \
                                "Jenkins CI"

                            git config \
                                user.email \
                                "jenkins@localhost"


                            git add \
                                app-deployment.yaml


                            if git diff \
                                --cached \
                                --quiet
                            then

                                echo "No GitOps image changes required."

                            else

                                git commit \
                                    -m "Update postgres-rag-ollama image to build $BUILD_NUMBER"

                                git push \
                                    origin \
                                    main

                            fi


                            echo "=========================================="
                            echo "GITOPS UPDATE SUCCESSFUL"
                            echo "=========================================="

                            echo "Argo CD will reconcile build $BUILD_NUMBER."
                        '''
                    }
                }
            }
        }
    }


    // ==========================================================
    // POST ACTIONS
    // ==========================================================

    post {


        // ======================================================
        // SUCCESS
        // ======================================================

        success {

            echo '''
==========================================
CI/CD PIPELINE SUCCESS
==========================================

Docker Image : SUCCESS
Docker Push  : SUCCESS
GitOps       : SUCCESS

Argo CD will synchronize automatically.

==========================================
'''


            script {

                try {

                    echo "Sending SUCCESS notification to Slack..."


                    container('git') {

                        withCredentials([

                            string(
                                credentialsId: 'postgres-rag-ollama-slack',
                                variable: 'SLACK_WEBHOOK'
                            )

                        ]) {

                            sh '''
                                set -e
                                set +x


                                if ! command -v curl >/dev/null 2>&1
                                then

                                    apk add \
                                        --no-cache \
                                        curl \
                                        >/dev/null 2>&1

                                fi


                                cat <<EOF | curl \
                                    --fail \
                                    --silent \
                                    --show-error \
                                    --connect-timeout 15 \
                                    --max-time 30 \
                                    -H 'Content-Type: application/json' \
                                    --data-binary @- \
                                    "$SLACK_WEBHOOK"
{
  "text": "✅ *POSTGRES RAG OLLAMA - DEPLOYMENT SUCCESS*\\n\\n*Build:* #${BUILD_NUMBER}\\n*Image:* docker.io/muskanpatel71198/postgres-rag-ollama:${BUILD_NUMBER}\\n*Docker:* Pushed successfully\\n*GitOps:* Updated successfully\\n*Argo CD:* Automatic synchronization initiated\\n*Build URL:* ${BUILD_URL}"
}
EOF


                                echo "Slack SUCCESS webhook completed."
                            '''
                        }
                    }


                    echo "Slack SUCCESS notification sent."

                }

                catch (Exception e) {

                    echo "=========================================="
                    echo "WARNING: Slack notification failed."
                    echo "Deployment itself was successful."
                    echo "Slack error: ${e.getMessage()}"
                    echo "=========================================="
                }
            }
        }


        // ======================================================
        // FAILURE
        // ======================================================

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

                    echo "Sending FAILURE notification to Slack..."


                    container('git') {

                        withCredentials([

                            string(
                                credentialsId: 'postgres-rag-ollama-slack',
                                variable: 'SLACK_WEBHOOK'
                            )

                        ]) {

                            sh '''
                                set -e
                                set +x


                                if ! command -v curl >/dev/null 2>&1
                                then

                                    apk add \
                                        --no-cache \
                                        curl \
                                        >/dev/null 2>&1

                                fi


                                cat <<EOF | curl \
                                    --fail \
                                    --silent \
                                    --show-error \
                                    --connect-timeout 15 \
                                    --max-time 30 \
                                    -H 'Content-Type: application/json' \
                                    --data-binary @- \
                                    "$SLACK_WEBHOOK"
{
  "text": "❌ *POSTGRES RAG OLLAMA - PIPELINE FAILED*\\n\\n*Build:* #${BUILD_NUMBER}\\n*Status:* FAILED\\n*Action:* Check Jenkins console logs\\n*Build URL:* ${BUILD_URL}"
}
EOF


                                echo "Slack FAILURE webhook completed."
                            '''
                        }
                    }


                    echo "Slack FAILURE notification sent."

                }

                catch (Exception e) {

                    echo "=========================================="
                    echo "WARNING: Slack notification failed."
                    echo "Original pipeline error is unchanged."
                    echo "Slack error: ${e.getMessage()}"
                    echo "=========================================="
                }
            }
        }


        // ======================================================
        // ALWAYS
        // ======================================================

        always {

            echo '''
==========================================
PIPELINE EXECUTION FINISHED
==========================================
'''
        }
    }
}