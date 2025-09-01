# Список селекторів для Twitter кнопок

## Кнопки репосту (Retweet)
- `button[data-testid="retweet"]` - основна кнопка репосту
- `div[data-testid="retweetConfirm"]` - кнопка підтвердження репосту

## Кнопки Quote (репост з коментарем)
- `a[role="menuitem"]` - кнопка Quote в меню репосту
- `div[data-testid="retweetConfirm"]` - альтернативна кнопка Quote
- `button[data-testid="retweetConfirm"]` - ще одна альтернатива

## Кнопки відправки поста
- `button[data-testid="tweetButton"]` - основна кнопка відправки
- `button[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-1cwvpvk r-2yi16 r-1qi8awa r-3pj75a r-1loqt21 r-o7ynqc r-6416eg r-jc7xae r-1ny4l3l"]` - кнопка відправки з повним класом

## Кнопки лайку
- `button[data-testid="like"]` - кнопка лайку

## Кнопки коментування
- `button[data-testid="reply"]` - кнопка коментування

## Поля введення тексту
- `div[aria-label="Post text"]` - поле для введення тексту поста/коментаря

## Кнопки створення поста
- `a[aria-label="Post"]` - кнопка створення нового поста

## Елементи для отримання кількості
- `span[data-testid="app-text-transition-container"]` - контейнер з кількістю лайків/репостів/коментарів

## Елементи для отримання інформації про автора
- `[data-testid="User-Name"]` - інформація про користувача

## Елементи для отримання посилань
- `[data-testid="toast"]` - контейнер з посиланням після створення поста
- `a` - посилання в toast контейнері

## Альтернативні селектори для Quote
Можливі варіанти:
- `button[data-testid="retweetConfirm"]`
- `div[role="menuitem"]`
- `a[data-testid="retweetConfirm"]`
- `button[aria-label="Retweet with comment"]`
- `div[aria-label="Retweet with comment"]`

## Альтернативні селектори для кнопки відправки
Можливі варіанти:
- `button[data-testid="tweetButtonInline"]`
- `button[data-testid="postButton"]`
- `button[aria-label="Post"]`
- `button[class*="css-175oi2r"][class*="r-sdzlij"]`
