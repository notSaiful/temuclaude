#!/bin/bash
# Temuclaude — Oracle Cloud Free Tier Deployment Script
# Deploys the full daemon swarm to Oracle Cloud Free Tier (4 ARM cores, 24GB RAM)
# $0/month forever. Mumbai region for lowest latency to India.
#
# Prerequisites:
# 1. Oracle Cloud Free Tier account (https://www.oracle.com/cloud/free/)
# 2. OCI CLI installed: pip install oci-cli
# 3. OCI config at ~/.oci/config
# 4. SSH key pair
#
# Usage: bash deploy_oracle.sh

set -e

INSTANCE_NAME="temuclaude-prod"
REGION="ap-mumbai-1"  # Mumbai — closest to Nagpur
SHAPE="VM.Standard.A1.Flex"  # ARM — free tier (4 OCPUs, 24GB RAM)
IMAGE="Oracle-Linux-9-aarch64-2024.01-0"
SSH_KEY="${HOME}/.ssh/id_rsa.pub"

echo "=== Temuclaude Oracle Cloud Deployment ==="
echo "Region: $REGION (Mumbai — closest to India)"
echo "Shape: $SHAPE (4 ARM cores, 24GB RAM — FREE)"
echo "Cost: \$0/month forever"
echo ""

# Step 1: Check OCI CLI
if ! command -v oci &> /dev/null; then
    echo "ERROR: OCI CLI not installed. Run: pip install oci-cli"
    exit 1
fi

# Step 2: Create compartment (if not exists)
echo "[1/6] Checking compartment..."
COMPARTMENT_OCID=$(oci iam compartment list --query "data[?name=='temuclaude'].id | [0]" --raw-output 2>/dev/null || echo "")
if [ -z "$COMPARTMENT_OCID" ]; then
    echo "  Creating compartment 'temuclaude'..."
    TENANCY_OCID=$(oci iam compartment list --query "data[0].compartment-id" --raw-output)
    COMPARTMENT_OCID=$(oci iam compartment create \
        --compartment-id "$TENANCY_OCID" \
        --name temuclaude \
        --description "Temuclaude production" \
        --query "data.id" --raw-output)
    echo "  Waiting for compartment to be active..."
    sleep 30
fi
echo "  Compartment: $COMPARTMENT_OCID"

# Step 3: Create VCN and subnet
echo "[2/6] Creating network..."
VCN_OCID=$(oci network vcn create \
    --compartment-id "$COMPARTMENT_OCID" \
    --cidr-block "10.0.0.0/16" \
    --display-name "temuclaude-vcn" \
    --query "data.id" --raw-output 2>/dev/null || echo "")
if [ -z "$VCN_OCID" ]; then
    VCN_OCID=$(oci network vcn list --compartment-id "$COMPARTMENT_OCID" --query "data[?display-name=='temuclaude-vcn'].id | [0]" --raw-output)
fi
echo "  VCN: $VCN_OCID"

# Step 4: Create compute instance
echo "[3/6] Creating ARM compute instance (FREE TIER)..."
if [ ! -f "$SSH_KEY" ]; then
    echo "  ERROR: SSH key not found at $SSH_KEY"
    echo "  Run: ssh-keygen -t rsa -b 2048"
    exit 1
fi

PUB_KEY=$(cat "$SSH_KEY")
INSTANCE_OCID=$(oci compute instance launch \
    --compartment-id "$COMPARTMENT_OCID" \
    --availability-domain "$REGION-AD-1" \
    --shape "$SHAPE" \
    --shape-config "{\"ocpus\":4,\"memoryInGBs\":24}" \
    --display-name "$INSTANCE_NAME" \
    --source-image-id "$IMAGE" \
    --ssh-authorized-keys "[$PUB_KEY]" \
    --query "data.id" --raw-output 2>/dev/null || echo "PENDING")

if [ "$INSTANCE_OCID" = "PENDING" ] || [ -z "$INSTANCE_OCID" ]; then
    echo "  Instance creation pending (free tier limits may apply)"
    echo "  Check Oracle Cloud Console manually"
else
    echo "  Instance: $INSTANCE_OCID"
fi

# Step 5: Get public IP
echo "[4/6] Getting public IP..."
PUBLIC_IP=$(oci compute instance list-vnics \
    --instance-id "$INSTANCE_OCID" \
    --query "data[0].\"public-ip\"" --raw-output 2>/dev/null || echo "PENDING")
echo "  Public IP: $PUBLIC_IP"

# Step 6: Generate deployment instructions
echo "[5/6] Generating deployment script..."
cat > /tmp/temuclaude_remote_setup.sh << 'REMOTEEOF'
#!/bin/bash
# Run this on the Oracle Cloud instance after SSH login
set -e

# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip git

# Clone Temuclaude
git clone https://github.com/saifulhaque/temuclaude.git
cd temuclaude

# Install dependencies
pip3.11 install -r requirements.txt

# Install Ollama (free inference)
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull gpt-oss:120b:cloud
ollama pull glm-5.2:cloud

# Set up systemd service for daemon swarm
sudo tee /etc/systemd/system/temuclaude.service << 'SERVICE'
[Unit]
Description=Temuclaude Autonomous Daemon Swarm
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/temuclaude
ExecStart=/usr/bin/python3.11 research/scripts/master_control.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable temuclaude
sudo systemctl start temuclaude

echo "Temuclaude deployed! Status: systemctl status temuclaude"
REMOTEEOF

echo "  Remote setup script: /tmp/temuclaude_remote_setup.sh"

echo "[6/6] Deployment instructions:"
echo ""
echo "  1. SSH to instance: ssh opc@$PUBLIC_IP"
echo "  2. Upload and run: scp /tmp/temuclaude_remote_setup.sh opc@$PUBLIC_IP:~ && ssh opc@$PUBLIC_IP 'bash temuc_remote_setup.sh'"
echo "  3. The daemon swarm starts automatically via systemd"
echo "  4. Auto-restarts on crash. Runs 24/7. \$0/month."
echo ""
echo "=== Deployment ready ==="