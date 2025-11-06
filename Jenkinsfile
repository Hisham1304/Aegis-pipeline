pipeline {
  agent any

  environment {
    // Visible defaults; actual secrets injected by withCredentials
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
        script {
          // Use scm if available, otherwise fallback to default checkout
          if (binding.hasVariable('scm') && scm) {
            checkout([$class: 'GitSCM',
                      branches: scm.branches ?: [[name: '*/main']],
                      userRemoteConfigs: scm.userRemoteConfigs,
                      extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false]]
            ])
          } else {
            checkout scm
          }
        }
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
        sh 'docker buildx version || (docker buildx create --use && docker buildx version) || true'
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
            docker pull playerunknown23/aegis:latest || true

            echo "Running Aegis scanner container..."
            SCANNER_EXIT=0
            docker run --rm \
              -v "${WORKSPACE}:/app/target:ro" \
              -v "${WORKSPACE}/results:/app/results:rw" \
              -e AEGIS_API_KEY="${AEGIS_API_KEY}" \
              -e CONFIG_API_URL="${CONFIG_API_URL}" \
              -e GITHUB_REPOSITORY="${JOB_NAME}" \
              -e GITHUB_REF="${BRANCH_NAME:-unknown-ref}" \
              -e GITHUB_SHA="${GIT_COMMIT:-unknown-sha}" \
              playerunknown23/aegis:latest \
              /app/target \
              --api-key "${AEGIS_API_KEY}" \
              ${CONFIG_API_URL:+--config-api-url "${CONFIG_API_URL}"} \
              --parallel || SCANNER_EXIT=$?
            echo "Aegis exit code: $SCANNER_EXIT"
            # exit with same scanner exit code (so pipeline reflects scanner outcome)
            exit $SCANNER_EXIT
          '''
        }
      }
    }

    stage('Create summary & show on console') {
      steps {
        script {
          // find first summary file if present
          def summaryFile = sh(script: "ls results/scan_summary_*.json 2>/dev/null | head -n1 || true", returnStdout: true).trim()
          if (summaryFile) {
            echo "---- Aegis scan summary (from ${summaryFile}) ----"
            def summary = readJSON file: summaryFile

            echo "**Summary:**"
            echo "- Packages Found (SBOM): ${summary.summary?.packages_found ?: 'N/A'}"
            echo "- Vulnerabilities in Packages (SCA): ${summary.summary?.vulnerabilities_in_packages ?: 'N/A'}"
            echo "- Secrets Found: ${summary.summary?.secrets_found ?: 'N/A'}"
            echo "- Code Vulnerabilities: ${summary.summary?.code_vulnerabilities ?: 'N/A'}"
            echo ""
            echo "**Severity Breakdown:**"
            echo "- Critical: ${summary.summary?.critical_severity ?: 0}"
            echo "- High: ${summary.summary?.high_severity ?: 0}"
            echo "- Medium: ${summary.summary?.medium_severity ?: 0}"
            echo "- Low: ${summary.summary?.low_severity ?: 0}"

            if (summary.metadata?.quality_gate_passed != null) {
              if (summary.metadata.quality_gate_passed.toString() == 'true') {
                echo "Quality Gate: PASSED"
              } else {
                echo "Quality Gate: FAILED"
                def reasons = summary.metadata.quality_gate_reasons ?: []
                reasons.each { echo "- ${it}" }
              }
            }
          } else {
            echo "No scan_summary_*.json found in results/ — skipping summary print."
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'results/**', fingerprint: true
      script {
        def summaryFile = sh(script: "ls results/scan_summary_*.json 2>/dev/null | head -n1 || true", returnStdout: true).trim()
        if (summaryFile) {
          def summary = readJSON file: summaryFile
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
