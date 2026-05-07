--
-- PostgreSQL database dump
--

\restrict 7KFBcyc3uXKSqCj54DWY2l4jGwgdIqSaLdqi6DY7d6K2F5igcr8E9IbQaJ6Hy7y

-- Dumped from database version 17.9
-- Dumped by pg_dump version 17.9

-- Started on 2026-05-05 16:17:26

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 868 (class 1247 OID 16454)
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'BLIND_USER',
    'CARETAKER'
);


ALTER TYPE public.userrole OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 16438)
-- Name: detection_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detection_logs (
    id integer NOT NULL,
    stick_id character varying(20),
    object_name character varying(100),
    confidence double precision,
    image_url text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.detection_logs OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16437)
-- Name: detection_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detection_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detection_logs_id_seq OWNER TO postgres;

--
-- TOC entry 4844 (class 0 OID 0)
-- Dependencies: 223
-- Name: detection_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detection_logs_id_seq OWNED BY public.detection_logs.id;


--
-- TOC entry 222 (class 1259 OID 16425)
-- Name: location_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.location_history (
    id integer NOT NULL,
    stick_id character varying(20),
    lat double precision,
    lon double precision,
    battery integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.location_history OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16424)
-- Name: location_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.location_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.location_history_id_seq OWNER TO postgres;

--
-- TOC entry 4845 (class 0 OID 0)
-- Dependencies: 221
-- Name: location_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.location_history_id_seq OWNED BY public.location_history.id;


--
-- TOC entry 220 (class 1259 OID 16409)
-- Name: relationships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.relationships (
    caretaker_id integer NOT NULL,
    blind_user_id integer NOT NULL
);


ALTER TABLE public.relationships OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16399)
-- Name: sticks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sticks (
    stick_id character varying(20) NOT NULL,
    owner_id integer,
    status character varying(20)
);


ALTER TABLE public.sticks OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16388)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(100) NOT NULL,
    password_hash text NOT NULL,
    full_name character varying(100),
    role character varying(20),
    phone character varying(15),
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['blind_user'::character varying, 'caretaker'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16387)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 4846 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4665 (class 2604 OID 16441)
-- Name: detection_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_logs ALTER COLUMN id SET DEFAULT nextval('public.detection_logs_id_seq'::regclass);


--
-- TOC entry 4663 (class 2604 OID 16428)
-- Name: location_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_history ALTER COLUMN id SET DEFAULT nextval('public.location_history_id_seq'::regclass);


--
-- TOC entry 4662 (class 2604 OID 16391)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4838 (class 0 OID 16438)
-- Dependencies: 224
-- Data for Name: detection_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detection_logs (id, stick_id, object_name, confidence, image_url, "timestamp") FROM stdin;
\.


--
-- TOC entry 4836 (class 0 OID 16425)
-- Dependencies: 222
-- Data for Name: location_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.location_history (id, stick_id, lat, lon, battery, "timestamp") FROM stdin;
1	STK001	16.07	108.14	80	2026-04-06 10:02:22.313349
2	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:00.888887
3	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:05.882253
4	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:10.891686
5	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:15.884231
6	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:20.895101
7	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:25.885328
8	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:30.891319
9	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:35.888065
10	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:40.891344
11	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:45.889967
12	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:50.891018
13	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:03:55.893086
14	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:00.895658
15	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:05.927333
16	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:10.893812
17	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:15.893982
18	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:20.895244
19	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:25.895587
20	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:30.905743
21	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:35.898644
22	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:40.905078
23	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:45.909703
24	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:04:50.900793
25	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:08:47.161275
26	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:08:52.203814
27	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:08:57.162369
28	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:09:02.158807
29	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:09:07.159602
30	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:09:12.16077
31	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:09:17.164611
32	STK001	16.073242434234	108.15234234234	85	2026-04-06 04:09:22.181817
33	STK001	32.54545345	184.22344234	85	2026-04-06 04:09:42.745331
34	STK001	32.54545345	184.22344234	85	2026-04-06 04:09:47.739045
35	STK001	32.54545345	184.22344234	85	2026-04-06 04:09:52.740829
36	STK001	32.54545345	184.22344234	85	2026-04-06 04:09:57.738707
37	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:02.739025
38	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:07.742838
39	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:12.739996
40	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:17.743445
41	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:22.74409
42	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:27.752355
43	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:32.744068
44	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:37.744559
45	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:42.745283
46	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:47.753009
47	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:52.749351
48	STK001	32.54545345	184.22344234	85	2026-04-06 04:10:57.746635
49	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:02.750531
50	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:07.750371
51	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:12.750616
52	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:17.751862
53	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:22.751492
54	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:27.763338
55	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:32.752896
56	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:37.755651
57	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:42.764602
58	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:47.758149
59	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:52.75983
60	STK001	32.54545345	184.22344234	85	2026-04-06 04:11:57.760716
61	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:02.75968
62	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:07.770123
63	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:12.760639
64	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:17.7621
65	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:22.769765
66	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:27.765931
67	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:32.764571
68	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:37.772678
69	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:42.771555
70	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:47.765561
71	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:52.780311
72	STK001	32.54545345	184.22344234	85	2026-04-06 04:12:57.771538
73	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:02.769807
74	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:07.776587
75	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:12.770058
76	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:17.77576
77	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:22.783048
78	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:27.784042
79	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:32.774259
80	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:37.776924
81	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:42.783768
82	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:47.781323
83	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:52.798375
84	STK001	32.54545345	184.22344234	85	2026-04-06 04:13:57.789218
85	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:02.779008
86	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:07.780334
87	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:12.800371
88	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:17.783414
89	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:22.785464
90	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:27.78426
91	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:32.783604
92	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:37.784672
93	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:42.823406
94	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:47.790704
95	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:52.787788
96	STK001	32.54545345	184.22344234	85	2026-04-06 04:14:57.788992
97	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:02.789535
98	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:07.790781
99	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:12.795681
100	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:17.817407
101	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:22.800447
102	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:27.864489
103	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:32.943009
104	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:38.557716
105	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:43.026192
106	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:47.836915
107	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:52.867728
108	STK001	32.54545345	184.22344234	85	2026-04-06 04:15:57.799023
109	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:02.802914
110	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:07.804045
111	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:13.019991
112	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:17.885048
113	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:22.987197
114	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:27.82041
115	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:32.824827
116	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:37.812163
117	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:42.806157
118	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:47.807049
119	STK001	32.54545345	184.22344234	85	2026-04-06 04:16:52.812098
\.


--
-- TOC entry 4834 (class 0 OID 16409)
-- Dependencies: 220
-- Data for Name: relationships; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.relationships (caretaker_id, blind_user_id) FROM stdin;
\.


--
-- TOC entry 4833 (class 0 OID 16399)
-- Dependencies: 219
-- Data for Name: sticks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sticks (stick_id, owner_id, status) FROM stdin;
STK001	1	online
\.


--
-- TOC entry 4832 (class 0 OID 16388)
-- Dependencies: 218
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, password_hash, full_name, role, phone) FROM stdin;
1	test@gmail.com	123hash	Tuan Anh	blind_user	0123456789
\.


--
-- TOC entry 4847 (class 0 OID 0)
-- Dependencies: 223
-- Name: detection_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detection_logs_id_seq', 1, false);


--
-- TOC entry 4848 (class 0 OID 0)
-- Dependencies: 221
-- Name: location_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.location_history_id_seq', 119, true);


--
-- TOC entry 4849 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- TOC entry 4679 (class 2606 OID 16446)
-- Name: detection_logs detection_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_logs
    ADD CONSTRAINT detection_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4677 (class 2606 OID 16431)
-- Name: location_history location_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_history
    ADD CONSTRAINT location_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4675 (class 2606 OID 16413)
-- Name: relationships relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_pkey PRIMARY KEY (caretaker_id, blind_user_id);


--
-- TOC entry 4673 (class 2606 OID 16403)
-- Name: sticks sticks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sticks
    ADD CONSTRAINT sticks_pkey PRIMARY KEY (stick_id);


--
-- TOC entry 4669 (class 2606 OID 16398)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4671 (class 2606 OID 16396)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4680 (class 1259 OID 16452)
-- Name: idx_detection_stick; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_detection_stick ON public.detection_logs USING btree (stick_id);


--
-- TOC entry 4685 (class 2606 OID 16447)
-- Name: detection_logs detection_logs_stick_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_logs
    ADD CONSTRAINT detection_logs_stick_id_fkey FOREIGN KEY (stick_id) REFERENCES public.sticks(stick_id) ON DELETE CASCADE;


--
-- TOC entry 4684 (class 2606 OID 16432)
-- Name: location_history location_history_stick_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_history
    ADD CONSTRAINT location_history_stick_id_fkey FOREIGN KEY (stick_id) REFERENCES public.sticks(stick_id) ON DELETE CASCADE;


--
-- TOC entry 4682 (class 2606 OID 16419)
-- Name: relationships relationships_blind_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_blind_user_id_fkey FOREIGN KEY (blind_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4683 (class 2606 OID 16414)
-- Name: relationships relationships_caretaker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_caretaker_id_fkey FOREIGN KEY (caretaker_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4681 (class 2606 OID 16404)
-- Name: sticks sticks_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sticks
    ADD CONSTRAINT sticks_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2026-05-05 16:17:26

--
-- PostgreSQL database dump complete
--

\unrestrict 7KFBcyc3uXKSqCj54DWY2l4jGwgdIqSaLdqi6DY7d6K2F5igcr8E9IbQaJ6Hy7y

