const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: false,
  configureWebpack: {
    externals: {
      'electron': 'require("electron")'
    },
  },
})
