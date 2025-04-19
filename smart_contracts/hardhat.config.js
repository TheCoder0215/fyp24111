require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.28",
  networks: {
    sepolia: {
      url: "https://sepolia.infura.io/v3/5f294e4494ab4cf8a0c6cc0c5f6b7a49",
      accounts: ["57c16e7628b888b0fe37a3fcf70b2cb4cbc8c4d8d3474aaf80a7392d87eee981"]
    }
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY
  }
};
