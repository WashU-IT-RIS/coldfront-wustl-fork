import path from "node:path";
import { build } from "vite";
import baseConfig from "./vite.config.js";

const dirname = import.meta.dirname;

const components = ["UserAccessManagement"];

for (let component of components) {
  console.log("Building", component);
  let componentRoot = path.resolve(dirname, `./src/views/${component}`);
  let outDir = path.resolve(dirname, `./dist/${component}`);

  baseConfig.root = componentRoot;
  baseConfig.base = `/static/${component}`;
  baseConfig.build.outDir = outDir;
  await build(baseConfig);
}
