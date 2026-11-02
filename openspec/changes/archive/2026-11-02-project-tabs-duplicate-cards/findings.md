# findings

- 项目 48：product_creation_launch 仅 1 条（33），作品仅 93。
- PersistentProjectPage.tsx 210–219 行 9 个兄弟组件都是 key={project.id}；ProductLaunchPanel 只在 tab==="brief" 时渲染，「项目素材」子页出现它只能是重复 key 留下的旧节点。浏览器调试工具被占用，未能在页面上直接确认 DOM。
