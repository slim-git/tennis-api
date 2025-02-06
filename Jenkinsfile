pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Checkout the code from the repository
                git branch: 'master', url: 'https://github.com/slim-git/tennis-api/'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build the Docker image using the Dockerfile
                    sh 'docker build -t tennis_api .'
                }
            }
        }

        stage('Run Tests Inside Docker Container') {
            steps {
                withCredentials([
                    string(credentialsId: 'MLFLOW_SERVER_URI', variable: 'MLFLOW_SERVER_URI'),
                    string(credentialsId: 'AWS_ACCESS_KEY_ID', variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'AWS_SECRET_ACCESS_KEY', variable: 'AWS_SECRET_ACCESS_KEY'),
                    string(credentialsId: 'PG_USER', variable: 'PG_USER'),
                    string(credentialsId: 'PG_PASSWORD', variable: 'PG_PASSWORD'),
                    string(credentialsId: 'PG_HOST', variable: 'PG_HOST'),
                    string(credentialsId: 'PG_PORT', variable: 'PG_PORT'),
                    string(credentialsId: 'PG_DB', variable: 'PG_DB'),
                    string(credentialsId: 'PG_SSLMODE', variable: 'PG_SSLMODE')
                ]) {
                    // Write environment variables to a temporary file
                    // KEEP SINGLE QUOTE FOR SECURITY PURPOSES (MORE INFO HERE: https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#handling-credentials)
                    script {
                        writeFile file: 'env.list', text: '''
                        MLFLOW_SERVER_URI=${MLFLOW_SERVER_URI}
                        AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
                        AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
                        PG_USER=${PG_USER}
                        PG_PASSWORD=${PG_PASSWORD}
                        PG_HOST=${PG_HOST}
                        PG_PORT=${PG_PORT}
                        PG_DB=${PG_DB}
                        PG_SSLMODE=${PG_SSLMODE}
                        '''
                    }

                    // Run a temporary Docker container and pass env variables securely via --env-file
                    sh '''
                    docker run --rm --env-file env.list \
                    tennis_api \
                    bash -c "pytest --maxfail=1 --disable-warnings"
                    '''
                }
            }
        }
    }

    post {
        always {
            // Clean up workspace and remove dangling Docker images
            sh 'docker system prune -f'
        }
        success {
            withCredentials([
                string(credentialsId: 'HF_USERNAME', variable: 'HF_USERNAME'),
                string(credentialsId: 'HF_TOKEN', variable: 'HF_TOKEN')
            ]) {
                echo 'Pipeline completed successfully! Pushing to huggingFace'
                sh 'git push --force https://${HF_USERNAME}:${HF_TOKEN}@huggingface.co/spaces/${HF_USERNAME}/tennis-api master:main'
            }
        }
        failure {
            echo 'Pipeline failed. Check logs for errors.'
        }
    }
}
