//./smart_contracts/scripts/deploy.js
const hre = require("hardhat");

async function main() {
  console.log("Deploying CertificateRegistry...");

  const CertificateRegistry = await hre.ethers.getContractFactory("CertificateRegistry");
  const registry = await CertificateRegistry.deploy();
  
  // Wait for deployment to complete
  await registry.waitForDeployment();
  
  // Get the deployed contract address
  const address = await registry.getAddress();
  
  console.log("CertificateRegistry deployed to:", address);
  
  // Optional: Wait for a few block confirmations
  await registry.deploymentTransaction().wait(5);
  console.log("Deployment confirmed with 5 block confirmations");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});