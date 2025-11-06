pipeline {
  agent any

  environment {
    // Visible defaults; real secrets are injected via withCredentials
    AEGIS_API_KEY = ""
    CONFIG_API_URL = ""
  }

  options {
    timeout(time: 60, unit: 'MINUTES')
    ansiColor('xterm')
  }

  stages {
    stage('Prepare') {
      steps {
        echo "Workspace: ${env.WORKSPACE}"
        sh 'mkdir -p results'
      }
    }

    stage('Checkout') {
      steps {
        // Full clone (no shallow)
        checkout([$class: 'GitSCM',
                  branches: scm.branches ?: [[name: '*/main']],
                  userRemoteConfigs: scm.userRemoteConfigs,
                  extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false]]
        ])
      }
    }

    stage('Install jq') {
      steps {
        sh '''
          if ! command -v jq >/dev/null 2>&1; then
            echo "Installing jq..."
            if command -v apt-get >/dev/null 2>&1; then
              sudo apt-get update && sudo apt-get install -y jq
            elif command -v yum >/dev/null 2>&1; then
              sudo yum install -y jq
            else
              echo "No known package manager - please install jq on the agent"
              exit 1
            fi
          else
            echo "jq already installed"
          fi
        '''
      }
    }

    stage('Set up Docker Buildx') {
      steps {
        sh 'docker buildx version || (docker buildx create --use && docker buildx version)'
      }
    }

    stage('Run Security Scan (Docker)') {
      steps {
        withCredentials([
          string(credentialsId: 'aegis_api_key', variable: 'AEGIS_API_KEY'),
          string(credentialsId: 'config_api_url', variable: 'CONFIG_API_URL')
        ]) {
          sh '''
            set -euo pipefail
            mkdir -p results
            echo "Pulling Aegis image..."
            docker pull playerunknown23/aegis:latest

            echo "Running Aegis scanner container..."
            # capture exit code to handle quality gate without stopping pipeline immediately
            SCANNER_EXIT=0 || true
            docker run --rm \
              -v "${WORKSPACE}:/app/target:ro" \
              -v "${WORKSPACE}/results:/app/results:rw" \
              -e AEGIS_API_KEY="${AEGIS_API_KEY}" \
              -e CONFIG_API_URL="${CONFIG_API_URL}" \
              -e GITHUB_REPOSITORY="${JOB_NAME}" \
              -e GITHUB_REF="${BRANCH_NAME:-unknown-ref}" \
              -e GITHUB_SHA="${GIT_COMMIT?:unknown-sha}" \
              playerunknown23/aegis:latest \
              /app/target \
              --api-key "${AEGIS_API_KEY}" \
              ${CONFIG_API_URL:+--config-api-url "${CONFIG_API_URL}"} \
              --parallel || SCANNER_EXIT=$?
            echo "Aegis exit code: $SCANNER_EXIT"
            # leave files in results/ regardless of exit code
            exit $SCANNER_EXIT
          '''
        }
      }
    }

    stage('Create summary & show on console') {
      steps {
        sh '''
          set -euo pipefail
          SUMMARY_FILE=$(ls results/scan_summary_*.json 2>/dev/null | head -n1 || true)
          if [ -n "$SUMMARY_FILE" ]; then
            echo "---- Aegis scan summary (from $SUMMARY_FILE) ----"
            cat "$SUMMARY_FILE" | jq -r '
              "**Summary:**\n" +
              "- Packages Found (SBOM): \(.summary.packages_found)\n" +
              "- Vulnerabilities in Packages (SCA): \(.summary.vulnerabilities_in_packages)\n" +
              "- Secrets Found: \(.summary.secrets_found)\n" +
              "- Code Vulnerabilities: \(.summary.code_vulnerabilities)\n" +
              "\n**Severity Breakdown:**\n" +
              "- Critical: \(.summary.critical_severity)\n" +
              "- High: \(.summary.high_severity)\n" +
              "- Medium: \(.summary.medium_severity)\n" +
              "- Low: \(.summary.low_severity)\n"
          else
            echo "No scan_summary_*.json found in results/ — skipping summary print."
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'results/**', fingerprint: true
      script {
        def summaryFiles = sh(script: "ls results/scan_summary_*.json 2>/dev/null | head -n1 || true", returnStdout: true).trim()
        if (summaryFiles) {
          def summary = readJSON file: summaryFiles
          if (summary?.metadata?.quality_gate_passed != null) {
            if (summary.metadata.quality_gate_passed.toString() == 'true') {
              echo "Quality Gate: PASSED"
            } else {
              echo "Quality Gate: FAILED"
              def reasons = summary.metadata.quality_gate_reasons ?: []
              def reasonText = reasons.join('<br/>')
              currentBuild.description = "Aegis Quality Gate: FAILED<br/>${reasonText}"
              currentBuild.result = 'UNSTABLE'
            }
          } else {
            echo "No quality gate metadata present in scan summary."
          }
        } else {
          echo "No scan summary found to evaluate quality gate."
        }
      }
    }

    failure {
      echo "Build failed — results are archived and available under the build artifacts."
    }
  }
}