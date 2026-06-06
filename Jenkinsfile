pipeline {
    agent { label 'python' }

    parameters {
        choice(
            name: 'PYTEST_SCOPE',
            choices: ['smoke', 'ui', 'cloud_smoke', 'all'],
            description: 'Набор тестов: API smoke / UI / Mobile BS / all'
        )
    }

    environment {
        ALLURE_ENDPOINT = credentials('ALLURE_ENDPOINT')
        ALLURE_TOKEN = credentials('ALLURE_TOKEN')
        ALLURE_PROJECT_ID = '592'
        TRELLO_API_KEY = credentials('TRELLO_API_KEY')
        TRELLO_API_TOKEN = credentials('TRELLO_API_TOKEN')
        TRELLO_EMAIL = credentials('TRELLO_EMAIL')
        TRELLO_PASSWORD = credentials('TRELLO_PASSWORD')
        BROWSERSTACK_USERNAME = credentials('BROWSERSTACK_USERNAME')
        BROWSERSTACK_ACCESS_KEY = credentials('BROWSERSTACK_ACCESS_KEY')
        BROWSERSTACK_APP = credentials('BROWSERSTACK_APP')
        BROWSERSTACK_BUILD_NAME = "${JOB_NAME}-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    git clone https://github.com/shadow7971247/trello_api.git trello_api || true
                    git clone https://github.com/shadow7971247/trello_ui.git trello_ui || true
                    git clone https://github.com/shadow7971247/trello_mobile.git trello_mobile || true
                '''
            }
        }
        stage('API') {
            when { expression { params.PYTEST_SCOPE in ['smoke', 'all'] } }
            steps {
                dir('trello_api') {
                    sh 'pip install -r requirements.txt && pytest -m smoke --alluredir=../allure-results'
                }
            }
        }
        stage('UI') {
            when { expression { params.PYTEST_SCOPE in ['ui', 'all'] } }
            steps {
                dir('trello_ui') {
                    sh 'pip install -r requirements.txt && pytest -m ui --alluredir=../allure-results'
                }
            }
        }
        stage('Mobile BrowserStack') {
            when { expression { params.PYTEST_SCOPE in ['cloud_smoke', 'all'] } }
            steps {
                dir('trello_mobile') {
                    sh 'pip install -r requirements.txt && pytest -m cloud_smoke --run-context browserstack --alluredir=../allure-results'
                }
            }
        }
        stage('Allure TestOps') {
            steps {
                sh '''
                    allurectl upload --endpoint "$ALLURE_ENDPOINT" \
                      --token "$ALLURE_TOKEN" \
                      --project-id "$ALLURE_PROJECT_ID" \
                      --launch-name "trello-${BUILD_NUMBER}" \
                      allure-results
                '''
            }
        }
    }

    post {
        always {
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
    }
}
