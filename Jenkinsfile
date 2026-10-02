// Tests ZigbeeControl's backend and frontend in a Kubernetes Job, then builds the zigbee-control
// and zigbee-control-ui images and pins them into Zigbee2mqttDeploy, which Argo CD syncs to prd.
//
// The images are built from the tree the suite passed on, so `latest` is tagged at build time and
// there is no promote stage.
//
// Controller config:
//   - Job: ZigbeeControl/ZigbeeControl
//   - SCM: pvginkel/ZigbeeControl, branch main
//   - Script Path: Jenkinsfile

library identifier: 'JenkinsPipelineUtils', changelog: false

pipeline {
    agent {
        kubernetes {
            inheritFrom 'jenkins-agent kaniko'
            yamlMergeStrategy merge()
            yaml podYaml(templates: ['k8s'])
        }
    }

    options {
        disableConcurrentBuilds(abortPrevious: true)
        skipDefaultCheckout()
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                script {
                    // No data sidecars: the backend keeps no database and reaches Zigbee2MQTT
                    // through the Kubernetes API, and the Playwright harness boots the backend and
                    // the SSE gateway per worker.
                    modernApp.test(
                        job: 'zigbee-control-validation',
                        install: 'poetry install --no-interaction --without dev',
                        run: 'poetry run',
                        suites: ['backend', 'frontend'],
                        services: [],
                        env: [:],
                        secrets: [],
                    )
                }
            }
        }

        stage('Build zigbee-control image') {
            steps {
                container('kaniko') {
                    script {
                        helmCharts.kaniko2(
                            dockerfile: 'backend/Dockerfile',
                            context: 'backend',
                            destinations: [
                                "registry:5000/zigbee-control:${currentBuild.number}",
                                'registry:5000/zigbee-control:latest',
                            ]
                        )
                    }
                }
            }
        }

        stage('Build zigbee-control-ui image') {
            steps {
                // The frontend shows the commit it was built from, and its build context holds no
                // .git to read it from.
                sh 'git rev-parse HEAD > frontend/git-rev'
                container('kaniko') {
                    script {
                        helmCharts.kaniko2(
                            dockerfile: 'frontend/Dockerfile',
                            context: 'frontend',
                            destinations: [
                                "registry:5000/zigbee-control-ui:${currentBuild.number}",
                                'registry:5000/zigbee-control-ui:latest',
                            ]
                        )
                    }
                }
            }
        }

        stage('Write image pins') {
            steps {
                container('k8s') {
                    script {
                        cicd.writeVersionPins(repo: 'pvginkel/Zigbee2mqttDeploy', pins: [
                            'config/prd/values.yaml': [
                                'images.zigbeeControl': ":${currentBuild.number}",
                                'images.zigbeeControlUI': ":${currentBuild.number}",
                            ],
                        ])
                    }
                }
            }
        }
    }
}
