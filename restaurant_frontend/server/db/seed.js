'use strict';

const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const { db } = require('./database');

const seeds = [
  {
    id:          1,
    name:        '오레노라멘 본점',
    category:    'japanese',
    sub:         JSON.stringify(['라멘', '따뜻한 국물']),
    lat:         37.4995,
    lng:         127.0265,
    rating:      4.8,
    price:       '평균 11,000원',
    description: '닭육수 베이스의 뽀얀 토리파이탄 라멘이 일품. 미슐랭 빕구르망 계속 선정.',
    platforms:   JSON.stringify(['google', 'naver']),
    img:         'https://images.unsplash.com/photo-1569718212165-38118228df19?w=300',
  },
  {
    id:          2,
    name:        '은행골 신사점',
    category:    'japanese',
    sub:         JSON.stringify(['초밥']),
    lat:         37.5005,
    lng:         127.0345,
    rating:      4.5,
    price:       '특초밥 17,000원',
    description: '입에서 사르르 녹는 부드러운 샤리(밥)가 특징. 단맛이 강하고 참치뱃살이 훌륭함.',
    platforms:   JSON.stringify(['naver']),
    img:         'https://images.unsplash.com/photo-1553621042-f6e147245754?w=300',
  },
  {
    id:          3,
    name:        '하동관',
    category:    'korean',
    sub:         JSON.stringify(['국밥', '따뜻한 국물']),
    lat:         37.5075,
    lng:         127.0290,
    rating:      4.3,
    price:       '보통 15,000원 대',
    description: '맑고 개운한 국물의 한우 곰탕 전문점. 깍두기 국물을 부어 먹는 깍국이 별미.',
    platforms:   JSON.stringify(['naver']),
    img:         'https://images.unsplash.com/photo-1588675646184-f5b0b0b0b2ee?w=300',
  },
  {
    id:          4,
    name:        '파이어벨',
    category:    'western',
    sub:         JSON.stringify(['햄버거']),
    lat:         37.4982,
    lng:         127.0298,
    rating:      4.6,
    price:       '세트 16,000원대',
    description: '육즙 가득한 정통 수제 아메리칸 치즈버거. 구글 리뷰 평점이 꾸준히 높게 유지됨.',
    platforms:   JSON.stringify(['google']),
    img:         'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300',
  },
  {
    id:          5,
    name:        '엽기떡볶이',
    category:    'spicy',
    sub:         JSON.stringify(['떡볶이', '매운 요리']),
    lat:         37.4978,
    lng:         127.0275,
    rating:      4.2,
    price:       '기본 14,000원 (2~3인)',
    description: '스트레스 풀리는 자극적인 강렬한 매운맛. 동네마다 있는 보증된 배달 특화 맛집.',
    platforms:   JSON.stringify(['naver']),
    img:         null,
  },
];

const insert = db.prepare(`
  INSERT OR REPLACE INTO restaurants
    (id, name, category, sub, lat, lng, rating, price, description, platforms, img)
  VALUES
    (@id, @name, @category, @sub, @lat, @lng, @rating, @price, @description, @platforms, @img)
`);

const insertMany = db.transaction((rows) => {
  for (const row of rows) insert.run(row);
});

insertMany(seeds);
console.log(`Seeded ${seeds.length} restaurants into pickeat.db`);
