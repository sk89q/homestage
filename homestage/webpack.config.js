const webpack = require('webpack');
const WebpackNotifierPlugin = require('webpack-notifier');
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin');

module.exports = {
  entry: {
    bundle: './assets/js/main.js'
  },
  output: {
    path: require("path").resolve("./bundle"),
    filename: '[name].js',
    publicPath: '/bundle/'
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        query: {
          presets: ['@babel/env', '@babel/react', '@babel/flow'],
          plugins: [
            ["@babel/plugin-proposal-decorators", {"legacy": true}],
            "@babel/plugin-proposal-function-sent",
            "@babel/plugin-proposal-export-namespace-from",
            "@babel/plugin-proposal-numeric-separator",
            "@babel/plugin-proposal-throw-expressions",
            "@babel/plugin-syntax-dynamic-import",
            "@babel/plugin-syntax-import-meta",
            ["@babel/plugin-proposal-class-properties", {"loose": true}],
            "@babel/plugin-proposal-json-strings"
          ]
        }
      },
      {
        test: /\.css$/, loader: "style-loader!css-loader"
      },
      {
        test: /\.scss$/,
        loaders: ["style-loader", "css-loader", "sass-loader"]
      },
      {
        test: /\.(png|gif|jpe?g)(\?[^\?]*)?$/,
        loader: 'file-loader'
      },
      {
        test: /\.(ttf|eot|svg|woff2?)(\?[^\?]*)?$/,
        loader: 'file-loader'
      }
    ]
  },
  plugins: [
    new LodashModuleReplacementPlugin(),
    new webpack.ProvidePlugin({
      $: "jquery",
      jQuery: "jquery"
    }),
  ],
  node: {
    fs: 'empty'
  },
  watchOptions: {
    ignored: ['node_modules']
  }
};
