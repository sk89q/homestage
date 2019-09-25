const gulp = require('gulp');
const sass = require('gulp-sass');
const babel = require('gulp-babel');
const sourcemaps = require('gulp-sourcemaps');
const concat = require('gulp-concat');
const compiler = require('webpack');
const webpack = require('webpack-stream');
const minify = require('gulp-minify-css');
const uglify = require('gulp-uglify');
const filter = require('gulp-filter');
const gutil = require('gulp-util');
const notify = require("gulp-notify");

function _watch_css_rebuild() {
  return gulp.src('assets/stylesheets/**/*.scss')
    .pipe(sourcemaps.init())
    .pipe(sass({
      includePaths: require('node-bourbon').includePaths
    }).on('error', err => {
      notify().write(err);
    }))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./static/css/'))
    .on('error', function (error) {
      notify().write({
        message: error.message
      });
      this.emit('end');
      process.exit(1);
    })
    .pipe(notify({
      title: "HomeStage Gulp",
      message: "The CSS finished building.",
      onLast: true
    }));
}

gulp.task('watch:css', function () {
  _watch_css_rebuild();

  return gulp.watch('assets/stylesheets/**/*.scss', _watch_css_rebuild);
});

gulp.task('prod:css', function () {
  return gulp.src('assets/stylesheets/**/*.scss')
    .pipe(sass({
      includePaths: require('node-bourbon').includePaths
    }).on('error', sass.logError))
    .pipe(minify())
    .pipe(gulp.dest('./static/css/'))
});

gulp.task('watch:js', function () {
  const webpackConfig = require('./webpack.config.js');
  webpackConfig.watch = false;
  webpackConfig.mode = 'development';

  function _watch_js_rebuild() {
    return gulp.src('assets/js/main.js')
      .pipe(webpack(webpackConfig, compiler))
      .pipe(gulp.dest('./static/bundle/'))
      .on('error', function (error) {
        notify().write({
          message: error.message
        });
        this.emit('end');
        process.exit(1);
      })
      .pipe(notify({
        title: "HomeStage Gulp",
        message: "The JavaScript finished building.",
        onLast: true
      }));
  }

  _watch_js_rebuild();

  return gulp.watch('assets/js/**/*.*', _watch_js_rebuild);
});

gulp.task('prod:js', function () {
  const webpackConfig = require('./webpack.config.js');
  webpackConfig.mode = 'production';
  const jsOnly = filter(['**/*.js'], {restore: true});
  return gulp.src('assets/js/main.js')
    .pipe(webpack(webpackConfig))
    .pipe(jsOnly)
    .pipe(uglify())
    .pipe(jsOnly.restore)
    .pipe(gulp.dest('./static/bundle/'));
});

gulp.task('watch:assets', function () {
  function _watch_assets_rebuild() {
    return gulp.src('./assets/fonts/**/*', {base: './assets/fonts/'})
      .pipe(gulp.dest('./static/fonts/'))
      .pipe(notify({
        title: "HomeStage Gulp",
        message: "Assets uploaded.",
        onLast: true
      }));
  }

  _watch_assets_rebuild();

  return gulp.watch('./assets/fonts/**/*', _watch_assets_rebuild);
});

gulp.task('prod:assets', function () {
  return gulp.src('./assets/fonts/**/*', {base: './assets/fonts/'})
    .pipe(gulp.dest('./static/fonts/'))
});

gulp.task('prod', gulp.parallel('prod:assets', 'prod:css', 'prod:js'));

gulp.task('watch', gulp.parallel('watch:assets', 'watch:css', 'watch:js'));

gulp.task('default', gulp.series('watch'));
