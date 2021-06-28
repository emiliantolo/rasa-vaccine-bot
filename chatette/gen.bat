python -m chatette -f nlu.chatette -a rasa-md
rasa data convert nlu -f yaml --data=output/train/ --out=./
type output_converted.yml add_to_nlu.yml > ../data/nlu.yml
