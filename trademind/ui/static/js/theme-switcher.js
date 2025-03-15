/**
 * TradeMind Lite - 主题切换器
 * 
 * 这个脚本用于管理网站的主题切换功能
 */

// 主题类型
const THEMES = {
    EMERALD_GOLD: 'emerald-gold',
    SUNSET_OCEAN: 'sunset-ocean',
    AZURE_CREAM: 'azure-cream'
};

// 主题名称
const THEME_NAMES = {
    [THEMES.EMERALD_GOLD]: '翠影流金',
    [THEMES.SUNSET_OCEAN]: '曦潮映空',
    [THEMES.AZURE_CREAM]: '蓝沁云霁'
};

// 默认主题
const DEFAULT_THEME = THEMES.EMERALD_GOLD;

// 本地存储键名
const THEME_STORAGE_KEY = 'trademind-theme';

// 主题CSS文件路径
const THEME_CSS_FILES = {
    [THEMES.EMERALD_GOLD]: '/static/css/theme-emerald-gold.css',
    [THEMES.SUNSET_OCEAN]: '/static/css/theme-sunset-ocean.css',
    [THEMES.AZURE_CREAM]: '/static/css/theme-azure-cream.css'
};

// 主题图标
const THEME_ICONS = {
    [THEMES.EMERALD_GOLD]: 'bi-tree-fill',
    [THEMES.SUNSET_OCEAN]: 'bi-sunrise-fill',
    [THEMES.AZURE_CREAM]: 'bi-cloud-sun-fill'
};

/**
 * 主题管理类
 */
class ThemeManager {
    constructor() {
        this.currentTheme = this.getSavedTheme() || DEFAULT_THEME;
        this.themeLink = null;
        this.init();
    }

    /**
     * 初始化主题管理器
     */
    init() {
        // 创建主题样式链接元素
        this.themeLink = document.createElement('link');
        this.themeLink.rel = 'stylesheet';
        this.themeLink.id = 'theme-css';
        document.head.appendChild(this.themeLink);

        // 应用当前主题
        this.applyTheme(this.currentTheme);

        // 设置主题切换按钮状态
        this.updateToggleButton();

        // 监听主题切换按钮点击事件
        document.addEventListener('DOMContentLoaded', () => {
            // 创建主题选择下拉菜单
            this.createThemeDropdown();
            
            // 监听主题切换按钮点击
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', () => {
                    this.cycleTheme();
                });
            }
            
            // 监听主题选择事件
            document.querySelectorAll('.theme-option').forEach(option => {
                option.addEventListener('click', (e) => {
                    const theme = e.currentTarget.getAttribute('data-theme');
                    this.applyTheme(theme);
                });
            });
        });
    }

    /**
     * 创建主题选择下拉菜单
     */
    createThemeDropdown() {
        const dropdown = document.getElementById('theme-dropdown');
        if (!dropdown) return;
        
        // 清空现有内容
        dropdown.innerHTML = '';
        
        // 添加主题选项
        Object.keys(THEMES).forEach(key => {
            const theme = THEMES[key];
            const option = document.createElement('li');
            const link = document.createElement('a');
            link.className = 'dropdown-item theme-option';
            link.setAttribute('data-theme', theme);
            link.href = '#';
            
            // 创建图标
            const icon = document.createElement('i');
            icon.className = `bi ${THEME_ICONS[theme]} me-2`;
            link.appendChild(icon);
            
            // 添加主题名称
            const text = document.createTextNode(THEME_NAMES[theme]);
            link.appendChild(text);
            
            // 如果是当前主题，添加选中标记
            if (theme === this.currentTheme) {
                link.classList.add('active');
                const checkIcon = document.createElement('i');
                checkIcon.className = 'bi bi-check ms-2';
                link.appendChild(checkIcon);
            }
            
            option.appendChild(link);
            dropdown.appendChild(option);
        });
    }

    /**
     * 获取保存的主题
     * @returns {string} 主题名称
     */
    getSavedTheme() {
        return localStorage.getItem(THEME_STORAGE_KEY);
    }

    /**
     * 保存主题到本地存储
     * @param {string} theme 主题名称
     */
    saveTheme(theme) {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }

    /**
     * 应用主题
     * @param {string} theme 主题名称
     */
    applyTheme(theme) {
        if (!THEME_CSS_FILES[theme]) {
            console.error(`未知主题: ${theme}`);
            theme = DEFAULT_THEME;
        }

        this.themeLink.href = THEME_CSS_FILES[theme];
        this.currentTheme = theme;
        this.saveTheme(theme);
        
        // 更新body的data-theme属性
        document.body.setAttribute('data-theme', theme);
        
        // 更新主题切换按钮状态
        this.updateToggleButton();
        
        // 更新下拉菜单
        this.createThemeDropdown();
    }

    /**
     * 循环切换主题
     */
    cycleTheme() {
        const themes = Object.values(THEMES);
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.applyTheme(themes[nextIndex]);
    }

    /**
     * 更新主题切换按钮状态
     */
    updateToggleButton() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        
        if (themeToggle && themeIcon) {
            themeToggle.setAttribute('title', `当前: ${THEME_NAMES[this.currentTheme]}`);
            themeIcon.className = `bi ${THEME_ICONS[this.currentTheme]}`;
        }
    }
}

// 创建并导出主题管理器实例
const themeManager = new ThemeManager();

// 如果在其他脚本中需要访问主题管理器，可以通过window对象
window.themeManager = themeManager; 