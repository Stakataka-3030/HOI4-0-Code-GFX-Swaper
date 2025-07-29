# HOI4-0-Code-GFX-Swaper

<h2>文件查看器工具</h2>
        <p><b>作者：</b>Stakataka_3030</p>
        <p><b>Github地址：</b><a href="https://github.com/Stakataka-3030/HOI4-0-Code-GFX-Swaper/">https://github.com/Stakataka-3030/HOI4-0-Code-GFX-Swaper/</a></p>
        <p>此工具基于GPL2.0开源</p>
        <h3>使用说明：</h3>
        <ul>
            <li>点选特定文件可快速替换对应文件，您不需要手动保持名称或格式一致，工具会自动完成替换和格式修改</li>
            <li>导出和导入配置功能会记录绝对路径，因此请不要移动图片文件或mod文件，否则将不得不重新选择</li>
            <li>用文件资源管理器导航到steam安装路径\steamapps\workshop\content\394360\modid（您可以在创意工坊链接的末尾找到modid，应当是一串9位或10位数字）</li>
            <li>点选"导出mod文件"会要求您选择一个文件夹。工具会在该文件夹下生成gfx文件夹。您应当将gfx文件夹复制到您在启动器创建的mod的文件夹中。并在您mod的descriptor.mod中加入dependencies={"xxx"}，其中xxx为屏幕上方显示的mod名称。</li>
            <li>然后，您可以启动游戏进行测试。</li>
        </ul>

如果您的文件转化成dds时报错，请安装nvidia texture tools exporter
