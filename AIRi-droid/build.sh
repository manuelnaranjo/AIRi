#!/bin/bash

set -x 
set -e

source common.sh

ant clean
ant release
