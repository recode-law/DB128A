/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2023 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

const getStoredTheme = () => localStorage.getItem('theme');
const setStoredTheme = theme => localStorage.setItem('theme', theme);

const getPreferredTheme = () => {
    const storedTheme = getStoredTheme();
    if (storedTheme) {
        return storedTheme;
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const setTheme = theme => {
    if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-bs-theme', theme);
    }

    if (document.readyState === "complete") {
        update_custom_parts();
    }
};

setTheme(getPreferredTheme());

const showActiveTheme = (theme, focus = false) => {
    const themeSwitcher = document.querySelector('#bd-theme');

    if (!themeSwitcher) {
        return;
    }

    const themeSwitcherText = document.querySelector('#bd-theme-text');
    const activeThemeIcon = document.querySelector('#theme-icon-active');
    const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);
    const svgOfActiveBtn = btnToActive.querySelector('i').getAttribute('class');

    document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
        element.classList.remove('active');
        element.setAttribute('aria-pressed', 'false');
    })

    btnToActive.classList.add('active');
    btnToActive.setAttribute('aria-pressed', 'true');
    activeThemeIcon.setAttribute('class', svgOfActiveBtn);
    const themeSwitcherLabel = `${themeSwitcherText.textContent} (${btnToActive.dataset.bsThemeValue})`;
    themeSwitcher.setAttribute('aria-label', themeSwitcherLabel);

    if (focus) {
        themeSwitcher.focus();
    }
};

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme();
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
        setTheme(getPreferredTheme());
    }
});

window.addEventListener('DOMContentLoaded', () => {
    showActiveTheme(getPreferredTheme());
    update_custom_parts();

    document.querySelectorAll('[data-bs-theme-value]')
        .forEach(toggle => {
            toggle.addEventListener('click', () => {
                const theme = toggle.getAttribute('data-bs-theme-value');
                setStoredTheme(theme);
                setTheme(theme);
                showActiveTheme(theme, true);
            });
        });
});

function update_custom_parts() {
    update_meta_theme_color();
    update_google_chart_colors();
    update_friendly_captcha_color();
    update_prose_color();
}

function rgb_to_hex(rgb_color) {
    let rgb_color_number_strings = rgb_color.split('(')[1].split(')')[0].split(', ');
    let hex_color_values = rgb_color_number_strings.map(function(number_string) {
        let hex_string = parseInt(number_string).toString(16);
        return (hex_string.length === 1) ? '0'+hex_string : hex_string;
    })
    return "#"+hex_color_values.join("");
}

function get_theme_background_color() {
    let header = document.getElementById('header');
    let rgb_color = getComputedStyle(header).getPropertyValue('background-color');
    return rgb_to_hex(rgb_color);
}

function get_theme_text_color() {
    let header_text = document.getElementById('header').children[0].children[0];
    let rgb_color = getComputedStyle(header_text).getPropertyValue('color');
    return rgb_to_hex(rgb_color);
}

function update_meta_theme_color() {
    let theme_color_meta = document.getElementById('theme-color-meta');
    theme_color_meta.content = get_theme_background_color();
}

function update_google_chart_colors() {
    for (let rejection_chart of document.getElementsByClassName('google-chart')) {
        if (rejection_chart && rejection_chart.children.length !== 0) {
            let text_color = get_theme_text_color();

            let chart_svg_parts = rejection_chart.children[0].children[0].children[0].children[0].children;
            let chart_title = chart_svg_parts[1].children[0];
            chart_title.setAttribute('fill', text_color);

            let chart_legend = chart_svg_parts[2];
            for (let child_index = 1; child_index < chart_legend.children.length; child_index++) {
                for (let text of chart_legend.children[child_index].children[1].children) {
                    text.setAttribute('fill', text_color);
                }
            }
        }
    }
}

function update_friendly_captcha_color() {
    const theme = localStorage.getItem('theme');
    const container = document.getElementsByClassName('frc-captcha')[0];
    if (container) {
        if (theme === 'dark') {
            container.classList.add('dark');
        } else {
            container.classList.remove('dark');
        }
    }
}

function update_prose_color() {
    document.documentElement.style.setProperty("--prose-editor-background",
        window.getComputedStyle(document.documentElement).getPropertyValue('--bs-body-bg'));
    document.documentElement.style.setProperty("--prose-editor-foreground",
        window.getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color'));
    document.documentElement.style.setProperty("--prose-editor-border-color",
        window.getComputedStyle(document.documentElement).getPropertyValue('--bs-border-color'));
    document.documentElement.style.setProperty("--prose-editor-active-color",
        window.getComputedStyle(document.documentElement).getPropertyValue('--bs-primary'));
    document.documentElement.style.setProperty("--prose-editor-disabled-color",
        window.getComputedStyle(document.documentElement).getPropertyValue('--bs-body-bg'));
}